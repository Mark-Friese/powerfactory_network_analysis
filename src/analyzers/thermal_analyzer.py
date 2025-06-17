"""
Thermal loading analyzer for PowerFactory network elements.
"""

from typing import List, Dict, Any, Optional

from .base_analyzer import BaseAnalyzer
from ..models.network_element import NetworkElement, ElementType
from ..models.analysis_result import AnalysisResult, AnalysisType


class ThermalAnalyzer(BaseAnalyzer):
    """
    Analyzer for thermal loading of network elements.
    
    Analyzes lines, transformers, and other thermal equipment
    against configurable loading thresholds.
    """
    
    def __init__(self, pf_interface, config: Dict[str, Any]):
        """
        Initialize thermal analyzer.
        
        Args:
            pf_interface: PowerFactory interface instance
            config: Configuration dictionary
        """
        super().__init__(pf_interface, config)
        
        # Extract thermal limits from config
        thermal_config = config.get('analysis', {}).get('thermal_limits', {})
        self.default_limit = thermal_config.get('default', 90.0)
        self.element_limits = {
            ElementType.LINE: thermal_config.get('lines', self.default_limit),
            ElementType.TRANSFORMER_2W: thermal_config.get('transformers', self.default_limit),
            ElementType.TRANSFORMER_3W: thermal_config.get('transformers', self.default_limit),
            ElementType.COUPLER: thermal_config.get('cables', self.default_limit)
        }
        
        self.logger.info(f"Initialized thermal analyzer with default limit: {self.default_limit}%")
    
    def get_analysis_type(self) -> AnalysisType:
        """Get the analysis type for thermal analysis."""
        return AnalysisType.THERMAL
    
    def get_applicable_elements(self, elements: List[NetworkElement]) -> List[NetworkElement]:
        """
        Filter elements applicable to thermal analysis.
        
        Args:
            elements: List of all network elements
            
        Returns:
            List of thermal elements (lines, transformers, etc.)
        """
        return [element for element in elements if element.is_thermal_element and element.operational_status]
    
    def get_thermal_limit(self, element: NetworkElement) -> float:
        """
        Get thermal loading limit for specific element.
        
        Args:
            element: Network element
            
        Returns:
            Thermal loading limit in percentage
        """
        return self.element_limits.get(element.element_type, self.default_limit)
    
    def analyze_element(self, element: NetworkElement, contingency: Optional[str] = None) -> Optional[AnalysisResult]:
        """
        Analyze thermal loading of a single element.
        
        Args:
            element: Network element to analyze
            contingency: Contingency scenario name (if applicable)
            
        Returns:
            Analysis result or None if not applicable
        """
        if not element.is_thermal_element:
            return None
        
        # Get loading from PowerFactory
        loading = self.get_element_value(element, 'm:loading')
        if loading is None:
            self.logger.warning(f"Could not get loading for {element.name}")
            return None
        
        # Get applicable limit
        limit = self.get_thermal_limit(element)
        
        # Create metadata
        metadata = {
            'element_type_specific_limit': limit,
            'current_loading_percent': loading
        }
        
        # Get additional thermal data if available
        current = self.get_element_value(element, 'm:I:bus1')
        if current is not None:
            metadata['current_amps'] = current
        
        power = self.get_element_value(element, 'm:P:bus1')
        if power is not None:
            metadata['power_mw'] = power
        
        return self.create_analysis_result(
            element=element,
            value=loading,
            limit=limit,
            contingency=contingency,
            metadata=metadata
        )
    
    def analyze_by_element_type(self, elements: List[NetworkElement], element_type: ElementType, 
                               contingency: Optional[str] = None) -> List[AnalysisResult]:
        """
        Analyze elements of specific type.
        
        Args:
            elements: List of network elements
            element_type: Target element type
            contingency: Contingency scenario name
            
        Returns:
            List of analysis results for specified element type
        """
        filtered_elements = self.filter_by_element_type(elements, element_type)
        results = []
        for element in filtered_elements:
            result = self.analyze_element(element, contingency)
            if result is not None:
                results.append(result)
        return results
    
    def get_overloaded_elements(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """
        Get elements with thermal overloads.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of overloaded elements
        """
        return self.get_violations(results)
    
    def get_loading_statistics_by_type(self, results: List[AnalysisResult]) -> Dict[str, Dict[str, Any]]:
        """
        Get loading statistics grouped by element type.
        
        Args:
            results: List of analysis results
            
        Returns:
            Dictionary with statistics by element type
        """
        stats_by_type = {}
        
        for element_type in [ElementType.LINE, ElementType.TRANSFORMER_2W, ElementType.TRANSFORMER_3W]:
            type_results = [r for r in results if r.element.element_type == element_type]
            
            if type_results:
                loadings = [r.value for r in type_results]
                violations = [r for r in type_results if r.is_violation]
                
                stats_by_type[element_type.value] = {
                    'count': len(type_results),
                    'max_loading': max(loadings),
                    'min_loading': min(loadings),
                    'avg_loading': sum(loadings) / len(loadings),
                    'violations': len(violations),
                    'violation_rate': len(violations) / len(type_results) * 100,
                    'thermal_limit': self.element_limits.get(element_type, self.default_limit)
                }
        
        return stats_by_type
    
    def identify_critical_elements(self, results: List[AnalysisResult], threshold: float = 95.0) -> List[AnalysisResult]:
        """
        Identify elements with critical loading levels.
        
        Args:
            results: List of analysis results
            threshold: Critical loading threshold (percentage)
            
        Returns:
            List of critically loaded elements
        """
        return [result for result in results if result.value >= threshold]
    
    def get_loading_distribution(self, results: List[AnalysisResult], 
                                num_bins: int = 10) -> Dict[str, Any]:
        """
        Get distribution of loading levels.
        
        Args:
            results: List of analysis results
            num_bins: Number of bins for distribution
            
        Returns:
            Dictionary with loading distribution data
        """
        if not results:
            return {'bins': [], 'counts': []}
        
        loadings = [r.value for r in results]
        min_loading = min(loadings)
        max_loading = max(loadings)
        
        # Handle case where all loadings are the same
        if min_loading == max_loading:
            return {
                'bins': [min_loading, min_loading + 1],
                'counts': [len(results)],
                'total_elements': len(results)
            }
        
        # Create bins
        bin_width = (max_loading - min_loading) / num_bins
        bins = [min_loading + i * bin_width for i in range(num_bins + 1)]
        counts = [0] * num_bins
        
        # Count loadings in each bin
        for loading in loadings:
            bin_index = min(int((loading - min_loading) / bin_width), num_bins - 1)
            counts[bin_index] += 1
        
        return {
            'bins': bins,
            'counts': counts,
            'total_elements': len(results)
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate thermal analyzer configuration.
        
        Returns:
            True if configuration is valid
        """
        if not super().validate_configuration():
            return False
        
        try:
            # Check thermal limits configuration
            thermal_config = self.config.get('analysis', {}).get('thermal_limits', {})
            
            if not thermal_config:
                self.logger.warning("No thermal limits configuration found, using defaults")
            
            # Validate limit values
            for element_type, limit in self.element_limits.items():
                if not isinstance(limit, (int, float)) or limit <= 0 or limit > 200:
                    self.logger.error(f"Invalid thermal limit for {element_type.value}: {limit}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Thermal analyzer configuration validation failed: {e}")
            return False
