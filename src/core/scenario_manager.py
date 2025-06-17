"""
Scenario management for generation and loading variations.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .powerfactory_interface import PowerFactoryInterface
from ..models.network_element import NetworkElement
from ..utils.logger import AnalysisLogger


@dataclass
class ScenarioElement:
    """Represents an element in a scenario with its scaling factor."""
    name: str
    element_type: str  # PowerFactory type (ElmGenstat, ElmLod, etc.)
    scaling_factor: float
    original_value: Optional[float] = None


@dataclass
class Scenario:
    """Represents a complete scenario configuration."""
    name: str
    description: str
    elements: List[ScenarioElement]
    load_scaling: float = 1.0


class ScenarioManager:
    """
    Manages generation and loading scenarios for iterative analysis.
    
    This class handles the creation and application of different generation
    and loading scenarios for comprehensive network analysis.
    """
    
    def __init__(self, pf_interface: PowerFactoryInterface):
        """
        Initialize scenario manager.
        
        Args:
            pf_interface: PowerFactory interface instance
        """
        self.pf_interface = pf_interface
        self.logger = AnalysisLogger(__name__)
        self._original_values: Dict[str, float] = {}
        self._active_scenario: Optional[str] = None
    
    def create_bess_scenarios(self, bess_a_name: str, bess_b_name: str) -> List[Scenario]:
        """
        Create BESS export/import combination scenarios.
        
        Args:
            bess_a_name: Name of first BESS unit
            bess_b_name: Name of second BESS unit
        
        Returns:
            List of BESS scenarios for iterative analysis
        """
        scenarios = []
        
        # Define BESS B scaling factors to test
        bess_b_factors = [1.0, 0.8, 0.6, 0.4, 0.0, -0.4, -0.6, -0.8, -1.0]
        
        for factor in bess_b_factors:
            scenario_name = f"BESS_A_100_BESS_B_{int(factor*100)}"
            if factor < 0:
                scenario_name = f"BESS_A_100_BESS_B_neg{int(abs(factor)*100)}"
            
            description = f"BESS A 100% export, BESS B {factor*100}% "
            description += "export" if factor >= 0 else "import"
            
            scenario = Scenario(
                name=scenario_name,
                description=description,
                elements=[
                    ScenarioElement(bess_a_name, "ElmGenstat", 1.0),
                    ScenarioElement(bess_b_name, "ElmGenstat", factor)
                ]
            )
            scenarios.append(scenario)
        
        self.logger.info(f"Created {len(scenarios)} BESS scenarios")
        return scenarios
    
    def create_custom_scenarios(self, scenario_configs: List[Dict[str, Any]]) -> List[Scenario]:
        """
        Create scenarios from configuration.
        
        Args:
            scenario_configs: List of scenario configuration dictionaries
        
        Returns:
            List of configured scenarios
        """
        scenarios = []
        
        for config in scenario_configs:
            elements = []
            for element_config in config.get('elements', []):
                element = ScenarioElement(
                    name=element_config['name'],
                    element_type=element_config['type'],
                    scaling_factor=element_config['scaling_factor']
                )
                elements.append(element)
            
            scenario = Scenario(
                name=config['name'],
                description=config.get('description', ''),
                elements=elements,
                load_scaling=config.get('load_scaling', 1.0)
            )
            scenarios.append(scenario)
        
        self.logger.info(f"Created {len(scenarios)} custom scenarios")
        return scenarios
    
    def apply_scenario(self, scenario: Scenario) -> bool:
        """
        Apply a scenario to the PowerFactory model.
        
        Args:
            scenario: Scenario to apply
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Applying scenario: {scenario.name}")
            
            # Store original values if not already stored
            for element in scenario.elements:
                if element.name not in self._original_values:
                    pf_obj = self._get_powerfactory_object(element.name, element.element_type)
                    if pf_obj:
                        original_value = self._get_element_value(pf_obj, element.element_type)
                        if original_value is not None:
                            self._original_values[element.name] = original_value
                            element.original_value = original_value
            
            # Apply scaling factors
            success_count = 0
            for element in scenario.elements:
                if self._apply_element_scaling(element):
                    success_count += 1
                else:
                    self.logger.warning(f"Failed to apply scaling for {element.name}")
            
            # Apply load scaling if specified
            if scenario.load_scaling != 1.0:
                if not self._apply_load_scaling(scenario.load_scaling):
                    self.logger.warning("Failed to apply load scaling")
            
            if success_count == len(scenario.elements):
                self._active_scenario = scenario.name
                self.logger.debug(f"Successfully applied scenario: {scenario.name}")
                return True
            else:
                self.logger.warning(f"Partially applied scenario {scenario.name}: {success_count}/{len(scenario.elements)} elements")
                return False
            
        except Exception as e:
            self.logger.error(f"Error applying scenario {scenario.name}: {e}")
            return False
    
    def restore_original_values(self) -> bool:
        """
        Restore all elements to their original values.
        
        Returns:
            True if successful
        """
        try:
            success_count = 0
            total_count = len(self._original_values)
            
            for element_name, original_value in self._original_values.items():
                if self._restore_element_value(element_name, original_value):
                    success_count += 1
            
            self._active_scenario = None
            
            if success_count == total_count:
                self.logger.info("Restored all elements to original values")
                return True
            else:
                self.logger.warning(f"Restored {success_count}/{total_count} elements")
                return False
            
        except Exception as e:
            self.logger.error(f"Error restoring values: {e}")
            return False
    
    def get_active_scenario(self) -> Optional[str]:
        """Get the name of the currently active scenario."""
        return self._active_scenario
    
    def clear_stored_values(self) -> None:
        """Clear all stored original values."""
        self._original_values.clear()
        self._active_scenario = None
        self.logger.debug("Cleared stored original values")
    
    def _get_powerfactory_object(self, element_name: str, element_type: str) -> Any:
        """Get PowerFactory object by name and type."""
        try:
            # Use PowerFactory interface to find object
            search_pattern = f"{element_name}.{element_type}"
            objects = self.pf_interface.get_calc_relevant_objects(search_pattern)
            
            if objects:
                return objects[0]  # Return first match
            
            # If direct search fails, try broader search
            all_objects = self.pf_interface.get_calc_relevant_objects(f"*.{element_type}")
            for obj in all_objects:
                name = self.pf_interface.get_element_attribute(obj, 'loc_name')
                if name == element_name:
                    return obj
            
            self.logger.warning(f"PowerFactory object not found: {element_name} ({element_type})")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding PowerFactory object {element_name}: {e}")
            return None
    
    def _get_element_value(self, pf_obj: Any, element_type: str) -> Optional[float]:
        """Get the current value of an element."""
        try:
            if element_type == "ElmGenstat":
                # For generators/BESS, use active power setting
                return self.pf_interface.get_element_attribute(pf_obj, "pgini")
            elif element_type == "ElmLod":
                # For loads, use active power
                return self.pf_interface.get_element_attribute(pf_obj, "plini")
            elif element_type == "ElmPvsys":
                # For PV systems
                return self.pf_interface.get_element_attribute(pf_obj, "pgini")
            else:
                self.logger.warning(f"Unknown element type for value retrieval: {element_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting element value: {e}")
            return None
    
    def _apply_element_scaling(self, element: ScenarioElement) -> bool:
        """Apply scaling to a single element."""
        try:
            pf_obj = self._get_powerfactory_object(element.name, element.element_type)
            if not pf_obj or element.original_value is None:
                return False
            
            new_value = element.original_value * element.scaling_factor
            
            if element.element_type == "ElmGenstat":
                attr = "pgini"
            elif element.element_type == "ElmLod":
                attr = "plini"
            elif element.element_type == "ElmPvsys":
                attr = "pgini"
            else:
                self.logger.warning(f"Unknown element type for scaling: {element.element_type}")
                return False
            
            success = self.pf_interface.set_element_attribute(pf_obj, attr, new_value)
            if success:
                self.logger.debug(f"Applied scaling to {element.name}: {element.original_value} -> {new_value}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error applying scaling to {element.name}: {e}")
            return False
    
    def _apply_load_scaling(self, scaling_factor: float) -> bool:
        """Apply uniform load scaling."""
        try:
            load_objects = self.pf_interface.get_calc_relevant_objects("*.ElmLod")
            success_count = 0
            
            for load in load_objects:
                try:
                    # Store original if not already stored
                    load_name = self.pf_interface.get_element_attribute(load, 'loc_name')
                    if load_name and f"load_{load_name}" not in self._original_values:
                        original_p = self.pf_interface.get_element_attribute(load, "plini")
                        original_q = self.pf_interface.get_element_attribute(load, "qlini")
                        
                        if original_p is not None:
                            self._original_values[f"load_{load_name}_p"] = original_p
                        if original_q is not None:
                            self._original_values[f"load_{load_name}_q"] = original_q
                    
                    # Apply scaling
                    original_p = self._original_values.get(f"load_{load_name}_p")
                    original_q = self._original_values.get(f"load_{load_name}_q")
                    
                    if original_p is not None:
                        new_p = original_p * scaling_factor
                        if self.pf_interface.set_element_attribute(load, "plini", new_p):
                            success_count += 1
                    
                    if original_q is not None:
                        new_q = original_q * scaling_factor
                        self.pf_interface.set_element_attribute(load, "qlini", new_q)
                        
                except Exception as e:
                    self.logger.debug(f"Error scaling load {load_name}: {e}")
                    continue
            
            self.logger.info(f"Applied load scaling to {success_count} loads")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error applying load scaling: {e}")
            return False
    
    def _restore_element_value(self, element_name: str, original_value: float) -> bool:
        """Restore a single element to its original value."""
        try:
            # Handle different element naming patterns
            if element_name.startswith("load_"):
                # Load element restoration
                load_name = element_name.replace("load_", "").replace("_p", "").replace("_q", "")
                pf_obj = self._get_powerfactory_object(load_name, "ElmLod")
                
                if pf_obj:
                    if element_name.endswith("_p"):
                        attr = "plini"
                    elif element_name.endswith("_q"):
                        attr = "qlini"
                    else:
                        return False
                    
                    return self.pf_interface.set_element_attribute(pf_obj, attr, original_value)
            else:
                # Generator/BESS element restoration
                # Try different element types
                for element_type in ["ElmGenstat", "ElmLod", "ElmPvsys"]:
                    pf_obj = self._get_powerfactory_object(element_name, element_type)
                    if pf_obj:
                        if element_type == "ElmGenstat":
                            attr = "pgini"
                        elif element_type == "ElmLod":
                            attr = "plini"
                        elif element_type == "ElmPvsys":
                            attr = "pgini"
                        else:
                            continue
                        
                        return self.pf_interface.set_element_attribute(pf_obj, attr, original_value)
            
            self.logger.warning(f"Could not restore element: {element_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error restoring element {element_name}: {e}")
            return False
