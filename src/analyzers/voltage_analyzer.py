"""
Voltage analysis for PowerFactory network busbars and terminals.
"""

from typing import List, Dict, Any, Optional, Tuple

from .base_analyzer import BaseAnalyzer
from ..models.network_element import NetworkElement, ElementType, Region
from ..models.analysis_result import AnalysisResult, AnalysisType


class VoltageAnalyzer(BaseAnalyzer):
    """
    Analyzer for voltage levels at network busbars.
    
    Analyzes terminal voltages against regional and voltage level specific
    limits for both Scotland and England networks.
    """
    
    def __init__(self, pf_interface, config: Dict[str, Any]):
        """
        Initialize voltage analyzer.
        
        Args:
            pf_interface: PowerFactory interface instance
            config: Configuration dictionary
        """
        super().__init__(pf_interface, config)
        
        # Extract voltage limits from config
        voltage_config = config.get('analysis', {}).get('voltage_limits', {})
        self.voltage_limits = voltage_config
        
        # Default limits if not configured
        self.default_limits = {
            'min': 0.95,
            'max': 1.05
        }
        
        self.logger.info(f"Initialized voltage analyzer with regional limits")
        self.logger.debug(f"Voltage limits configuration: {self.voltage_limits}")
    
    def get_analysis_type(self) -> AnalysisType:
        """Get the analysis type for voltage analysis."""
        return AnalysisType.VOLTAGE
    
    def get_applicable_elements(self, elements: List[NetworkElement]) -> List[NetworkElement]:
        """
        Filter elements applicable to voltage analysis.
        
        Args:
            elements: List of all network elements
            
        Returns:
            List of voltage elements (busbars/terminals)
        """
        return [element for element in elements if element.is_voltage_element and element.operational_status]
    
    def get_voltage_limits(self, element: NetworkElement) -> Tuple[float, float]:
        """
        Get voltage limits for specific element based on region and voltage level.
        
        Args:
            element: Network element
            
        Returns:
            Tuple of (min_limit, max_limit) in per unit
        """
        # Get regional limits
        regional_limits = self.voltage_limits.get(element.region.value, {})
        
        # Get voltage level specific limits
        voltage_str = str(float(element.voltage_level))
        level_limits = regional_limits.get(voltage_str, self.default_limits)
        
        min_limit = level_limits.get('min', self.default_limits['min'])
        max_limit = level_limits.get('max', self.default_limits['max'])
        
        return min_limit, max_limit
    
    def analyze_element(self, element: NetworkElement, contingency: Optional[str] = None) -> Optional[AnalysisResult]:
        """
        Analyze voltage of a single busbar element.
        
        Args:
            element: Network element to analyze
            contingency: Contingency scenario name (if applicable)
            
        Returns:
            Analysis result or None if not applicable
        """
        if not element.is_voltage_element:
            return None
        
        # Get voltage from PowerFactory (per unit)
        voltage_pu = self.get_element_value(element, 'm:u')
        if voltage_pu is None:
            self.logger.warning(f"Could not get voltage for {element.name}")
            return None
        
        # Get voltage limits
        min_limit, max_limit = self.get_voltage_limits(element)
        
        # Determine which limit is violated (if any)
        violation_type = None
        limit_used = None
        
        if voltage_pu < min_limit:
            violation_type = "undervoltage"
            limit_used = min_limit
        elif voltage_pu > max_limit:
            violation_type = "overvoltage" 
            limit_used = max_limit
        else:
            # Use the closer limit for analysis
            if abs(voltage_pu - min_limit) < abs(voltage_pu - max_limit):
                limit_used = min_limit
                violation_type = "normal_low"
            else:
                limit_used = max_limit
                violation_type = "normal_high"
        
        # Create metadata
        metadata = {
            'voltage_pu': voltage_pu,
            'min_limit': min_limit,
            'max_limit': max_limit,
            'violation_type': violation_type,
            'region': element.region.value,
            'voltage_level_kv': element.voltage_level
        }
        
        # Get additional voltage data if available
        voltage_kv = self.get_element_value(element, 'm:U')
        if voltage_kv is not None:
            metadata['voltage_kv'] = voltage_kv
        
        angle = self.get_element_value(element, 'm:phiu')
        if angle is not None:
            metadata['angle_deg'] = angle
        
        return self.create_analysis_result(
            element=element,
            value=voltage_pu,
            limit=limit_used,
            contingency=contingency,
            metadata=metadata
        )
    
    def analyze_by_region(self, elements: List[NetworkElement], region: Region, 
                         contingency: Optional[str] = None) -> List[AnalysisResult]:
        """
        Analyze elements in specific region.
        
        Args:
            elements: List of network elements
            region: Target region
            contingency: Contingency scenario name
            
        Returns:
            List of analysis results for specified region
        """
        filtered_elements = self.filter_by_region(elements, region)
        results = []
        for element in filtered_elements:
            result = self.analyze_element(element, contingency)
            if result is not None:
                results.append(result)
        return results
    
    def analyze_by_voltage_level(self, elements: List[NetworkElement], voltage_level: float,
                                contingency: Optional[str] = None) -> List[AnalysisResult]:
        """
        Analyze elements at specific voltage level.
        
        Args:
            elements: List of network elements
            voltage_level: Target voltage level in kV
            contingency: Contingency scenario name
            
        Returns:
            List of analysis results for specified voltage level
        """
        filtered_elements = self.filter_by_voltage_level(elements, voltage_level)
        results = []
        for element in filtered_elements:
            result = self.analyze_element(element, contingency)
            if result is not None:
                results.append(result)
        return results
    
    def get_voltage_violations(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """
        Get elements with voltage violations.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of voltage violations
        """
        return self.get_violations(results)
    
    def get_undervoltage_violations(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """
        Get elements with undervoltage violations.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of undervoltage violations
        """
        return [result for result in results 
                if result.is_violation and result.metadata.get('violation_type') == 'undervoltage']
    
    def get_overvoltage_violations(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """
        Get elements with overvoltage violations.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of overvoltage violations
        """
        return [result for result in results 
                if result.is_violation and result.metadata.get('violation_type') == 'overvoltage']
    
    def get_voltage_statistics_by_region(self, results: List[AnalysisResult]) -> Dict[str, Dict[str, Any]]:
        """
        Get voltage statistics grouped by region.
        
        Args:
            results: List of analysis results
            
        Returns:
            Dictionary with statistics by region
        """
        stats_by_region = {}
        
        for region in [Region.SCOTLAND, Region.ENGLAND]:
            region_results = [r for r in results if r.element.region == region]
            
            if region_results:
                voltages = [r.value for r in region_results]
                violations = [r for r in region_results if r.is_violation]
                undervoltages = [r for r in violations if r.metadata.get('violation_type') == 'undervoltage']
                overvoltages = [r for r in violations if r.metadata.get('violation_type') == 'overvoltage']
                
                stats_by_region[region.value] = {
                    'count': len(region_results),
                    'max_voltage': max(voltages),
                    'min_voltage': min(voltages),
                    'avg_voltage': sum(voltages) / len(voltages),
                    'total_violations': len(violations),
                    'undervoltage_violations': len(undervoltages),
                    'overvoltage_violations': len(overvoltages),
                    'violation_rate': len(violations) / len(region_results) * 100
                }
        
        return stats_by_region
    
    def get_voltage_statistics_by_level(self, results: List[AnalysisResult]) -> Dict[str, Dict[str, Any]]:
        """
        Get voltage statistics grouped by voltage level.
        
        Args:
            results: List of analysis results
            
        Returns:
            Dictionary with statistics by voltage level
        """
        stats_by_level = {}
        
        # Group results by voltage level
        voltage_levels = set(r.element.voltage_level for r in results)
        
        for level in voltage_levels:
            level_results = [r for r in results if r.element.voltage_level == level]
            
            if level_results:
                voltages = [r.value for r in level_results]
                violations = [r for r in level_results if r.is_violation]
                
                # Get limits for this voltage level (use first element of this level)
                sample_element = level_results[0].element
                min_limit, max_limit = self.get_voltage_limits(sample_element)
                
                stats_by_level[f"{level}kV"] = {
                    'count': len(level_results),
                    'max_voltage': max(voltages),
                    'min_voltage': min(voltages),
                    'avg_voltage': sum(voltages) / len(voltages),
                    'violations': len(violations),
                    'violation_rate': len(violations) / len(level_results) * 100,
                    'min_limit': min_limit,
                    'max_limit': max_limit
                }
        
        return stats_by_level
    
    def identify_critical_voltage_buses(self, results: List[AnalysisResult], 
                                       threshold: float = 0.02) -> List[AnalysisResult]:
        """
        Identify buses with critically low or high voltages.
        
        Args:
            results: List of analysis results
            threshold: Threshold from limits (per unit)
            
        Returns:
            List of critically loaded buses
        """
        critical_buses = []
        
        for result in results:
            min_limit, max_limit = self.get_voltage_limits(result.element)
            
            # Check if voltage is critically close to limits
            if (result.value <= min_limit + threshold or 
                result.value >= max_limit - threshold):
                critical_buses.append(result)
        
        return critical_buses
    
    def get_voltage_profile(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Get voltage profile across the network.
        
        Args:
            results: List of analysis results
            
        Returns:
            Dictionary with voltage profile data
        """
        if not results:
            return {'voltage_levels': [], 'voltages': [], 'bus_names': [], 'regions': []}
        
        # Sort by voltage level then by voltage value
        sorted_results = sorted(results, key=lambda r: (r.element.voltage_level, r.value))
        
        return {
            'voltage_levels': [r.element.voltage_level for r in sorted_results],
            'voltages': [r.value for r in sorted_results],
            'bus_names': [r.element.name for r in sorted_results],
            'regions': [r.element.region.value for r in sorted_results]
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate voltage analyzer configuration.
        
        Returns:
            True if configuration is valid
        """
        if not super().validate_configuration():
            return False
        
        try:
            # Check voltage limits configuration
            if not self.voltage_limits:
                self.logger.warning("No voltage limits configuration found, using defaults")
            
            # Validate regional configurations
            for region_name, region_config in self.voltage_limits.items():
                if region_name not in ['scotland', 'england']:
                    self.logger.warning(f"Unknown region in configuration: {region_name}")
                    continue
                
                # Validate voltage level configurations
                for voltage_level, limits in region_config.items():
                    min_limit = limits.get('min')
                    max_limit = limits.get('max')
                    
                    if not isinstance(min_limit, (int, float)) or not isinstance(max_limit, (int, float)):
                        self.logger.error(f"Invalid voltage limits for {region_name} {voltage_level}kV")
                        return False
                    
                    if min_limit >= max_limit:
                        self.logger.error(f"Min limit >= max limit for {region_name} {voltage_level}kV")
                        return False
                    
                    if min_limit <= 0 or max_limit <= 0:
                        self.logger.error(f"Invalid voltage limit values for {region_name} {voltage_level}kV")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Voltage analyzer configuration validation failed: {e}")
            return False
