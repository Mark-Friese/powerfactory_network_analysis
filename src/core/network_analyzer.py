"""
Main network analyzer orchestrating thermal and voltage analysis.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .powerfactory_interface import PowerFactoryInterface
from .contingency_manager import ContingencyManager
from ..analyzers.thermal_analyzer import ThermalAnalyzer
from ..analyzers.voltage_analyzer import VoltageAnalyzer
from ..models.network_element import NetworkElement, ElementType, Region
from ..models.analysis_result import AnalysisResult, AnalysisType
from ..utils.logger import AnalysisLogger


class NetworkAnalyzer:
    """
    Main orchestrator for PowerFactory network analysis.
    
    Coordinates thermal and voltage analysis across different regions,
    manages contingency scenarios, and aggregates results.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize network analyzer.
        
        Args:
            config_path: Path to analysis configuration file
        """
        self.logger = AnalysisLogger(self.__class__.__name__)
        
        # Load configuration
        if config_path:
            self.config = self._load_config(config_path)
        else:
            # Default configuration paths
            config_dir = Path(__file__).parent.parent.parent / "config"
            self.config = self._load_default_configs(config_dir)
        
        # Initialize PowerFactory interface
        self.pf_interface = PowerFactoryInterface()
        
        # Initialize analyzers
        self.thermal_analyzer = ThermalAnalyzer(self.pf_interface, self.config)
        self.voltage_analyzer = VoltageAnalyzer(self.pf_interface, self.config)
        
        # Initialize contingency manager
        self.contingency_manager = ContingencyManager(self.pf_interface)
        
        # Analysis results storage
        self.base_case_results: Dict[str, List[AnalysisResult]] = {
            'thermal': [],
            'voltage': []
        }
        self.contingency_results: Dict[str, Dict[str, List[AnalysisResult]]] = {}
        
        # Network elements cache
        self._network_elements: Optional[List[NetworkElement]] = None
        
        self.logger.info("Network analyzer initialized successfully")
    
    def _load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_default_configs(self, config_dir: Path) -> Dict[str, Any]:
        """Load default configuration files."""
        config = {}
        
        # Load analysis config
        analysis_config_path = config_dir / "analysis_config.yaml"
        if analysis_config_path.exists():
            with open(analysis_config_path, 'r') as f:
                config.update(yaml.safe_load(f))
        
        # Load network config
        network_config_path = config_dir / "network_config.yaml"
        if network_config_path.exists():
            with open(network_config_path, 'r') as f:
                config.update(yaml.safe_load(f))
        
        self.logger.info("Loaded default configuration files")
        return config
    
    def connect_to_powerfactory(self) -> bool:
        """
        Connect to PowerFactory and validate connection.
        
        Returns:
            True if connection successful
        """
        self.logger.info("Connecting to PowerFactory...")
        
        if not self.pf_interface.connect():
            self.logger.error("Failed to connect to PowerFactory")
            return False
        
        if not self.pf_interface.validate_connection():
            self.logger.error("PowerFactory connection validation failed")
            return False
        
        # Log network statistics
        stats = self.pf_interface.get_network_statistics()
        self.logger.info(f"Network statistics: {stats}")
        
        return True
    
    def load_network_elements(self, force_reload: bool = False) -> List[NetworkElement]:
        """
        Load network elements from PowerFactory.
        
        Args:
            force_reload: Force reload of elements even if cached
            
        Returns:
            List of network elements
        """
        if self._network_elements is not None and not force_reload:
            return self._network_elements
        
        self.logger.info("Loading network elements from PowerFactory...")
        
        elements = []
        
        # Get element type configurations
        element_config = self.config.get('element_types', {})
        region_config = self.config.get('regions', {})
        
        # Load thermal elements
        thermal_types = element_config.get('thermal_elements', ['ElmLne', 'ElmTr2', 'ElmTr3', 'ElmCoup'])
        for pf_type in thermal_types:
            pf_objects = self.pf_interface.get_calc_relevant_objects(f'*.{pf_type}')
            for obj in pf_objects:
                element = self._create_network_element(obj, pf_type, region_config)
                if element:
                    elements.append(element)
        
        # Load voltage elements
        voltage_types = element_config.get('voltage_elements', ['ElmTerm'])
        for pf_type in voltage_types:
            pf_objects = self.pf_interface.get_calc_relevant_objects(f'*.{pf_type}')
            for obj in pf_objects:
                element = self._create_network_element(obj, pf_type, region_config)
                if element:
                    elements.append(element)
        
        # Filter based on configuration
        elements = self._filter_elements(elements)
        
        self._network_elements = elements
        self.logger.info(f"Loaded {len(elements)} network elements")
        
        return elements
    
    def _create_network_element(self, pf_object: Any, pf_type: str, region_config: Dict) -> Optional[NetworkElement]:
        """Create NetworkElement from PowerFactory object."""
        try:
            # Get basic properties
            name = self.pf_interface.get_element_attribute(pf_object, 'loc_name')
            if not name:
                return None
            
            # Determine element type
            element_type = ElementType(pf_type)
            
            # Get voltage level
            voltage_level = self._get_element_voltage_level(pf_object, element_type)
            if voltage_level is None:
                return None
            
            # Determine region based on voltage level and configuration
            region = self._determine_element_region(voltage_level, region_config)
            
            # Check operational status
            out_of_service = self.pf_interface.get_element_attribute(pf_object, 'outserv')
            operational_status = not bool(out_of_service)
            
            return NetworkElement(
                name=name,
                element_type=element_type,
                voltage_level=voltage_level,
                region=region,
                powerfactory_object=pf_object,
                operational_status=operational_status
            )
            
        except Exception as e:
            self.logger.debug(f"Error creating network element: {e}")
            return None
    
    def _get_element_voltage_level(self, pf_object: Any, element_type: ElementType) -> Optional[float]:
        """Get voltage level for PowerFactory object."""
        try:
            if element_type == ElementType.BUSBAR:
                # For terminals, get nominal voltage directly
                uknom = self.pf_interface.get_element_attribute(pf_object, 'uknom')
                return float(uknom) if uknom else None
            else:
                # For other elements, get from connected terminal
                bus1 = self.pf_interface.get_element_attribute(pf_object, 'bus1')
                if bus1:
                    uknom = self.pf_interface.get_element_attribute(bus1, 'uknom')
                    return float(uknom) if uknom else None
        except Exception:
            pass
        return None
    
    def _determine_element_region(self, voltage_level: float, region_config: Dict) -> Region:
        """Determine region based on voltage level and configuration."""
        # Default logic: Scotland for 33kV and 11kV, England for 132kV and others
        scotland_levels = region_config.get('scotland', {}).get('voltage_levels', [33.0, 11.0])
        england_levels = region_config.get('england', {}).get('voltage_levels', [132.0, 33.0, 11.0])
        
        if voltage_level in scotland_levels and voltage_level not in [132.0]:
            return Region.SCOTLAND
        else:
            return Region.ENGLAND
    
    def _filter_elements(self, elements: List[NetworkElement]) -> List[NetworkElement]:
        """Filter elements based on configuration."""
        filters = self.config.get('filters', {})
        
        filtered = elements
        
        # Filter out of service elements if configured
        if filters.get('exclude_out_of_service', True):
            filtered = [e for e in filtered if e.operational_status]
        
        # Filter minimum voltage level
        min_voltage = filters.get('minimum_voltage_level', 1.0)
        filtered = [e for e in filtered if e.voltage_level >= min_voltage]
        
        return filtered
    
    def run_base_case_analysis(self) -> Dict[str, List[AnalysisResult]]:
        """
        Run base case analysis (thermal and voltage).
        
        Returns:
            Dictionary with thermal and voltage analysis results
        """
        self.logger.info("Starting base case analysis...")
        
        # Ensure PowerFactory connection
        if not self.pf_interface.is_connected:
            if not self.connect_to_powerfactory():
                raise RuntimeError("Cannot connect to PowerFactory")
        
        # Load network elements
        elements = self.load_network_elements()
        
        # Execute load flow
        self.logger.info("Executing base case load flow...")
        if not self.pf_interface.execute_load_flow():
            self.logger.error("Base case load flow failed")
            raise RuntimeError("Load flow execution failed")
        
        results = {}
        
        # Run thermal analysis
        if self.config.get('analysis', {}).get('options', {}).get('run_thermal', True):
            self.logger.info("Running thermal analysis...")
            results['thermal'] = self.thermal_analyzer.analyze_network(elements)
            self.logger.info(f"Thermal analysis completed: {len(results['thermal'])} results")
        
        # Run voltage analysis
        if self.config.get('analysis', {}).get('options', {}).get('run_voltage', True):
            self.logger.info("Running voltage analysis...")
            results['voltage'] = self.voltage_analyzer.analyze_network(elements)
            self.logger.info(f"Voltage analysis completed: {len(results['voltage'])} results")
        
        self.base_case_results = results
        self.logger.info("Base case analysis completed")
        
        return results
    
    def run_contingency_analysis(self) -> Dict[str, Dict[str, List[AnalysisResult]]]:
        """
        Run N-1 contingency analysis.
        
        Returns:
            Dictionary with contingency results
        """
        if not self.config.get('analysis', {}).get('options', {}).get('run_contingency', True):
            self.logger.info("Contingency analysis disabled in configuration")
            return {}
        
        self.logger.info("Starting contingency analysis...")
        
        # Get network elements
        elements = self.load_network_elements()
        
        # Get contingencies
        contingencies = self.contingency_manager.get_n1_contingencies()
        max_contingencies = self.config.get('analysis', {}).get('options', {}).get('max_contingencies', 1000)
        
        if len(contingencies) > max_contingencies:
            self.logger.info(f"Limiting contingencies to {max_contingencies}")
            contingencies = contingencies[:max_contingencies]
        
        contingency_results = {}
        
        for i, contingency_name in enumerate(contingencies, 1):
            self.logger.info(f"Running contingency {i}/{len(contingencies)}: {contingency_name}")
            
            try:
                # Apply contingency
                success = self.contingency_manager.apply_contingency(contingency_name)
                if not success:
                    self.logger.warning(f"Failed to apply contingency: {contingency_name}")
                    continue
                
                # Execute load flow
                if not self.pf_interface.execute_load_flow():
                    self.logger.warning(f"Load flow failed for contingency: {contingency_name}")
                    continue
                
                # Run analysis
                results = {}
                results['thermal'] = self.thermal_analyzer.analyze_network(elements, contingency_name)
                results['voltage'] = self.voltage_analyzer.analyze_network(elements, contingency_name)
                
                contingency_results[contingency_name] = results
                
                # Restore system
                self.contingency_manager.restore_system()
                
            except Exception as e:
                self.logger.error(f"Error in contingency analysis for {contingency_name}: {e}")
                # Attempt to restore system
                self.contingency_manager.restore_system()
        
        self.contingency_results = contingency_results
        self.logger.info(f"Contingency analysis completed: {len(contingency_results)} contingencies analyzed")
        
        return contingency_results
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Run complete analysis including base case and contingencies.
        
        Returns:
            Complete analysis results
        """
        self.logger.info("Starting full network analysis...")
        start_time = datetime.now()
        
        # Validate configuration
        if not self._validate_analysis_configuration():
            raise RuntimeError("Analysis configuration validation failed")
        
        # Connect to PowerFactory
        if not self.connect_to_powerfactory():
            raise RuntimeError("Failed to connect to PowerFactory")
        
        # Run base case analysis
        base_case_results = self.run_base_case_analysis()
        
        # Run contingency analysis
        contingency_results = self.run_contingency_analysis()
        
        # Compile results
        analysis_results = {
            'timestamp': start_time,
            'analysis_duration': datetime.now() - start_time,
            'base_case': base_case_results,
            'contingencies': contingency_results,
            'configuration': self.config,
            'network_statistics': self.pf_interface.get_network_statistics()
        }
        
        self.logger.info(f"Full analysis completed in {analysis_results['analysis_duration']}")
        
        return analysis_results
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of analysis results.
        
        Returns:
            Analysis summary statistics
        """
        summary = {
            'base_case': {},
            'contingencies': {},
            'violations': {}
        }
        
        # Base case summary
        if self.base_case_results:
            for analysis_type, results in self.base_case_results.items():
                if analysis_type == 'thermal':
                    summary['base_case']['thermal'] = self.thermal_analyzer.get_summary_statistics(results)
                elif analysis_type == 'voltage':
                    summary['base_case']['voltage'] = self.voltage_analyzer.get_summary_statistics(results)
        
        # Contingency summary
        if self.contingency_results:
            total_contingencies = len(self.contingency_results)
            contingencies_with_violations = 0
            
            for contingency_name, results in self.contingency_results.items():
                has_violations = False
                for analysis_type, result_list in results.items():
                    violations = [r for r in result_list if r.is_violation]
                    if violations:
                        has_violations = True
                
                if has_violations:
                    contingencies_with_violations += 1
            
            summary['contingencies'] = {
                'total_analyzed': total_contingencies,
                'with_violations': contingencies_with_violations,
                'violation_rate': (contingencies_with_violations / total_contingencies * 100) if total_contingencies > 0 else 0
            }
        
        return summary
    
    def _validate_analysis_configuration(self) -> bool:
        """Validate analysis configuration."""
        try:
            # Validate analyzer configurations
            if not self.thermal_analyzer.validate_configuration():
                return False
            
            if not self.voltage_analyzer.validate_configuration():
                return False
            
            # Validate analysis options
            options = self.config.get('analysis', {}).get('options', {})
            run_base_case = options.get('run_base_case', True)  # Default to True
            run_contingency = options.get('run_contingency', True)  # Default to True
            
            if not run_base_case and not run_contingency:
                self.logger.error("At least one of base case or contingency analysis must be enabled")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def filter_elements_by_area(self, elements: List[NetworkElement], area_pattern: str) -> List[NetworkElement]:
        """
        Filter network elements by geographic area.
        
        Args:
            elements: List of network elements
            area_pattern: Pattern to match (e.g., "Glenrothes*")
        
        Returns:
            Filtered list of elements for the specified area
        """
        import fnmatch
        
        filtered_elements = []
        for element in elements:
            # Check if element name matches area pattern
            if fnmatch.fnmatch(element.name, area_pattern):
                filtered_elements.append(element)
            
            # Also check parent grid/substation if available
            try:
                if hasattr(element.powerfactory_object, 'GetParent'):
                    parent = element.powerfactory_object.GetParent()
                    if parent:
                        parent_name = self.pf_interface.get_element_attribute(parent, 'loc_name')
                        if parent_name and fnmatch.fnmatch(parent_name, area_pattern):
                            filtered_elements.append(element)
                            continue
            except Exception:
                pass  # Ignore errors in parent checking
        
        # Remove duplicates
        unique_elements = []
        seen_names = set()
        for element in filtered_elements:
            if element.name not in seen_names:
                unique_elements.append(element)
                seen_names.add(element.name)
        
        self.logger.info(f"Filtered to {len(unique_elements)} elements for area: {area_pattern}")
        return unique_elements
    
    def get_network_elements(self) -> List[NetworkElement]:
        """Get loaded network elements."""
        if self._network_elements is None:
            return self.load_network_elements()
        return self._network_elements
    
    def disconnect(self) -> None:
        """Disconnect from PowerFactory."""
        self.pf_interface.disconnect()
        self.logger.info("Disconnected from PowerFactory")
