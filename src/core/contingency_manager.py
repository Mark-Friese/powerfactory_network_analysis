"""
Contingency management for N-1 analysis operations.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .powerfactory_interface import PowerFactoryInterface
from ..models.network_element import NetworkElement
from ..utils.logger import AnalysisLogger


class ContingencyStatus(Enum):
    """Status of contingency operation."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ContingencyState:
    """
    Represents the state of a network element during contingency analysis.
    
    Attributes:
        element: Network element
        original_status: Original operational status
        contingency_status: Current contingency status
        error_message: Error message if operation failed
    """
    element: NetworkElement
    original_status: bool
    contingency_status: ContingencyStatus = ContingencyStatus.PENDING
    error_message: Optional[str] = None


class ContingencyManager:
    """
    Manages N-1 contingency analysis operations.
    
    Handles element outages, restoration, and state tracking for
    comprehensive contingency analysis scenarios.
    """
    
    def __init__(self, pf_interface: PowerFactoryInterface):
        """
        Initialize contingency manager.
        
        Args:
            pf_interface: PowerFactory interface instance
        """
        self.pf_interface = pf_interface
        self.logger = AnalysisLogger(__name__)
        self._contingency_states: Dict[str, ContingencyState] = {}
        self._active_contingency: Optional[str] = None
    
    def prepare_contingency_list(self, elements: List[NetworkElement]) -> List[NetworkElement]:
        """
        Prepare list of elements for contingency analysis.
        
        Args:
            elements: List of network elements to analyze
            
        Returns:
            Filtered list of elements suitable for contingency analysis
        """
        contingency_elements = []
        
        for element in elements:
            # Only include thermal elements that are in service
            if element.is_thermal_element and element.operational_status:
                # Store original state
                self._contingency_states[element.name] = ContingencyState(
                    element=element,
                    original_status=element.operational_status
                )
                contingency_elements.append(element)
                
        self.logger.info(f"Prepared {len(contingency_elements)} elements for contingency analysis")
        return contingency_elements
    
    def apply_contingency_element(self, element: NetworkElement) -> bool:
        """
        Apply contingency (take element out of service).
        
        Args:
            element: Element to take out of service
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if another contingency is active
            if self._active_contingency and self._active_contingency != element.name:
                self.logger.warning(f"Another contingency '{self._active_contingency}' is active")
                return False
            
            # Apply outage
            success = element.set_out_of_service(True)
            
            if success:
                self._active_contingency = element.name
                if element.name in self._contingency_states:
                    self._contingency_states[element.name].contingency_status = ContingencyStatus.ACTIVE
                self.logger.debug(f"Applied contingency: {element.name}")
                return True
            else:
                if element.name in self._contingency_states:
                    self._contingency_states[element.name].contingency_status = ContingencyStatus.FAILED
                    self._contingency_states[element.name].error_message = "Failed to set out of service"
                self.logger.error(f"Failed to apply contingency: {element.name}")
                return False
                
        except Exception as e:
            if element.name in self._contingency_states:
                self._contingency_states[element.name].contingency_status = ContingencyStatus.FAILED
                self._contingency_states[element.name].error_message = str(e)
            self.logger.error(f"Error applying contingency {element.name}: {e}")
            return False
    
    def restore_contingency(self, element: NetworkElement) -> bool:
        """
        Restore element from contingency (put back in service).
        
        Args:
            element: Element to restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if element.name not in self._contingency_states:
                self.logger.warning(f"Element {element.name} not in contingency state tracking")
                return False
            
            original_status = self._contingency_states[element.name].original_status
            success = element.set_out_of_service(not original_status)
            
            if success:
                self._contingency_states[element.name].contingency_status = ContingencyStatus.COMPLETED
                if self._active_contingency == element.name:
                    self._active_contingency = None
                self.logger.debug(f"Restored contingency: {element.name}")
                return True
            else:
                self._contingency_states[element.name].contingency_status = ContingencyStatus.FAILED
                self._contingency_states[element.name].error_message = "Failed to restore service"
                self.logger.error(f"Failed to restore contingency: {element.name}")
                return False
                
        except Exception as e:
            if element.name in self._contingency_states:
                self._contingency_states[element.name].contingency_status = ContingencyStatus.FAILED
                self._contingency_states[element.name].error_message = str(e)
            self.logger.error(f"Error restoring contingency {element.name}: {e}")
            return False
    
    def restore_all_contingencies(self) -> bool:
        """
        Restore all elements to their original states.
        
        Returns:
            True if all elements restored successfully
        """
        success_count = 0
        total_count = len(self._contingency_states)
        
        for state in self._contingency_states.values():
            if self.restore_contingency(state.element):
                success_count += 1
        
        self._active_contingency = None
        
        if success_count == total_count:
            self.logger.info("All contingencies restored successfully")
            return True
        else:
            self.logger.warning(f"Restored {success_count}/{total_count} contingencies")
            return False
    
    def run_contingency_analysis(
        self, 
        elements: List[NetworkElement],
        analysis_callback: callable,
        max_contingencies: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run complete N-1 contingency analysis.
        
        Args:
            elements: Elements to analyze
            analysis_callback: Function to call for each contingency
            max_contingencies: Maximum number of contingencies to analyze
            
        Returns:
            Dictionary with analysis results and statistics
        """
        self.logger.start_operation("N-1 Contingency Analysis")
        
        # Prepare contingency list
        contingency_elements = self.prepare_contingency_list(elements)
        
        if max_contingencies:
            contingency_elements = contingency_elements[:max_contingencies]
        
        total_contingencies = len(contingency_elements)
        successful_contingencies = 0
        failed_contingencies = 0
        analysis_results = []
        
        # Run base case first
        self.logger.info("Running base case analysis")
        try:
            if self.pf_interface.execute_load_flow():
                base_results = analysis_callback("base_case")
                if base_results:
                    analysis_results.extend(base_results)
            else:
                self.logger.error("Base case load flow failed")
        except Exception as e:
            self.logger.error(f"Base case analysis failed: {e}")
        
        # Run contingency analysis
        for i, element in enumerate(contingency_elements, 1):
            self.logger.log_progress(i, total_contingencies, f"Analyzing {element.name}")
            
            try:
                # Apply contingency
                if not self.apply_contingency(element):
                    failed_contingencies += 1
                    continue
                
                # Run load flow
                if not self.pf_interface.execute_load_flow():
                    self.logger.warning(f"Load flow failed for contingency: {element.name}")
                    self.restore_contingency(element)
                    failed_contingencies += 1
                    continue
                
                # Run analysis
                contingency_results = analysis_callback(element.name)
                if contingency_results:
                    analysis_results.extend(contingency_results)
                
                # Restore contingency
                self.restore_contingency(element)
                successful_contingencies += 1
                
            except Exception as e:
                self.logger.error(f"Error in contingency {element.name}: {e}")
                self.restore_contingency(element)  # Ensure restoration
                failed_contingencies += 1
        
        # Final restoration
        self.restore_all_contingencies()
        
        # Compile results
        results = {
            'total_contingencies': total_contingencies,
            'successful_contingencies': successful_contingencies,
            'failed_contingencies': failed_contingencies,
            'analysis_results': analysis_results,
            'contingency_states': {name: state for name, state in self._contingency_states.items()}
        }
        
        self.logger.complete_operation(
            f"N-1 Analysis: {successful_contingencies}/{total_contingencies} successful",
            success=(failed_contingencies == 0)
        )
        
        return results
    
    def get_contingency_status(self, element_name: str) -> Optional[ContingencyStatus]:
        """
        Get status of specific contingency.
        
        Args:
            element_name: Name of element
            
        Returns:
            Contingency status or None if not found
        """
        if element_name in self._contingency_states:
            return self._contingency_states[element_name].contingency_status
        return None
    
    def get_failed_contingencies(self) -> List[Tuple[str, str]]:
        """
        Get list of failed contingencies.
        
        Returns:
            List of tuples (element_name, error_message)
        """
        failed = []
        for name, state in self._contingency_states.items():
            if state.contingency_status == ContingencyStatus.FAILED:
                failed.append((name, state.error_message or "Unknown error"))
        return failed
    
    def get_n1_contingencies(self) -> List[str]:
        """
        Get list of N-1 contingency scenarios.
        
        Returns:
            List of contingency element names
        """
        if not self.pf_interface.is_connected:
            self.logger.error("PowerFactory not connected")
            return []
        
        contingency_elements = []
        
        # Get thermal elements for contingency analysis
        thermal_classes = ['*.ElmLne', '*.ElmTr2', '*.ElmTr3', '*.ElmCoup']
        
        for pf_class in thermal_classes:
            elements = self.pf_interface.get_calc_relevant_objects(pf_class)
            for element in elements:
                # Check if element is in service
                out_of_service = self.pf_interface.get_element_attribute(element, 'outserv')
                if not out_of_service:  # Element is in service
                    element_name = self.pf_interface.get_element_attribute(element, 'loc_name')
                    if element_name:
                        contingency_elements.append(element_name)
        
        self.logger.info(f"Found {len(contingency_elements)} elements for N-1 contingency analysis")
        return contingency_elements
    
    def apply_contingency(self, contingency_name: str) -> bool:
        """
        Apply contingency by element name.
        
        Args:
            contingency_name: Name of element to take out of service
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find element by name
            thermal_classes = ['*.ElmLne', '*.ElmTr2', '*.ElmTr3', '*.ElmCoup']
            target_element = None
            
            for pf_class in thermal_classes:
                elements = self.pf_interface.get_calc_relevant_objects(pf_class)
                for element in elements:
                    element_name = self.pf_interface.get_element_attribute(element, 'loc_name')
                    if element_name == contingency_name:
                        target_element = element
                        break
                if target_element:
                    break
            
            if not target_element:
                self.logger.error(f"Contingency element not found: {contingency_name}")
                return False
            
            # Store original state
            original_status = not bool(self.pf_interface.get_element_attribute(target_element, 'outserv'))
            
            # Apply outage
            success = self.pf_interface.set_element_attribute(target_element, 'outserv', 1)
            
            if success:
                self._active_contingency = contingency_name
                self.logger.debug(f"Applied contingency: {contingency_name}")
                return True
            else:
                self.logger.error(f"Failed to apply contingency: {contingency_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error applying contingency {contingency_name}: {e}")
            return False
    
    def restore_system(self) -> bool:
        """
        Restore system from current contingency.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._active_contingency:
            return True  # No active contingency to restore
        
        try:
            # Find element by name
            thermal_classes = ['*.ElmLne', '*.ElmTr2', '*.ElmTr3', '*.ElmCoup']
            target_element = None
            
            for pf_class in thermal_classes:
                elements = self.pf_interface.get_calc_relevant_objects(pf_class)
                for element in elements:
                    element_name = self.pf_interface.get_element_attribute(element, 'loc_name')
                    if element_name == self._active_contingency:
                        target_element = element
                        break
                if target_element:
                    break
            
            if not target_element:
                self.logger.error(f"Cannot find element to restore: {self._active_contingency}")
                return False
            
            # Restore element (put back in service)
            success = self.pf_interface.set_element_attribute(target_element, 'outserv', 0)
            
            if success:
                self.logger.debug(f"Restored contingency: {self._active_contingency}")
                self._active_contingency = None
                return True
            else:
                self.logger.error(f"Failed to restore contingency: {self._active_contingency}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring contingency {self._active_contingency}: {e}")
            return False
    
    def clear_contingency_states(self) -> None:
        """Clear all contingency state tracking."""
        self._contingency_states.clear()
        self._active_contingency = None
        self.logger.debug("Cleared contingency states")
