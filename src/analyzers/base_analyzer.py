"""
Base analyzer class providing common functionality for all analysis types.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.powerfactory_interface import PowerFactoryInterface
from ..models.network_element import NetworkElement, ElementType, Region
from ..models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
from ..utils.logger import AnalysisLogger


class BaseAnalyzer(ABC):
    """
    Abstract base class for all network analyzers.
    
    Provides common functionality and interface for specialized analyzers.
    """
    
    def __init__(self, pf_interface: PowerFactoryInterface, config: Dict[str, Any]):
        """
        Initialize base analyzer.
        
        Args:
            pf_interface: PowerFactory interface instance
            config: Configuration dictionary
        """
        self.pf_interface = pf_interface
        self.config = config
        self.logger = AnalysisLogger(self.__class__.__name__)
        self.results: List[AnalysisResult] = []
    
    @abstractmethod
    def get_analysis_type(self) -> AnalysisType:
        """Get the analysis type for this analyzer."""
        pass
    
    @abstractmethod
    def analyze_element(self, element: NetworkElement, contingency: Optional[str] = None) -> Optional[AnalysisResult]:
        """
        Analyze a single network element.
        
        Args:
            element: Network element to analyze
            contingency: Contingency scenario name (if applicable)
            
        Returns:
            Analysis result or None if not applicable
        """
        pass
    
    @abstractmethod
    def get_applicable_elements(self, elements: List[NetworkElement]) -> List[NetworkElement]:
        """
        Filter elements applicable to this analyzer.
        
        Args:
            elements: List of all network elements
            
        Returns:
            List of applicable elements
        """
        pass
    
    def analyze_network(self, elements: List[NetworkElement], contingency: Optional[str] = None) -> List[AnalysisResult]:
        """
        Analyze multiple network elements.
        
        Args:
            elements: List of network elements to analyze
            contingency: Contingency scenario name (if applicable)
            
        Returns:
            List of analysis results
        """
        applicable_elements = self.get_applicable_elements(elements)
        results = []
        
        self.logger.start_operation(
            f"{self.get_analysis_type().value} analysis",
            len(applicable_elements)
        )
        
        for i, element in enumerate(applicable_elements, 1):
            try:
                result = self.analyze_element(element, contingency)
                if result:
                    results.append(result)
                    
                if i % 10 == 0:  # Progress every 10 elements
                    self.logger.log_progress(i, len(applicable_elements))
                    
            except Exception as e:
                self.logger.error(f"Error analyzing {element.name}: {e}")
        
        self.logger.complete_operation(f"{self.get_analysis_type().value} analysis")
        return results
    
    def get_element_value(self, element: NetworkElement, attribute: str) -> Optional[float]:
        """
        Get numerical value from PowerFactory element.
        
        Args:
            element: Network element
            attribute: PowerFactory attribute name
            
        Returns:
            Attribute value or None if not available
        """
        try:
            value = self.pf_interface.get_element_attribute(element.powerfactory_object, attribute)
            if value is not None:
                return float(value)
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Could not convert {attribute} to float for {element.name}: {e}")
        return None
    
    def determine_result_status(self, value: float, limit: float, analysis_type: AnalysisType) -> ResultStatus:
        """
        Determine result status based on value and limit.
        
        Args:
            value: Measured value
            limit: Applicable limit
            analysis_type: Type of analysis
            
        Returns:
            Result status
        """
        try:
            if analysis_type == AnalysisType.THERMAL:
                # For thermal analysis, violation is when value > limit
                if value > limit:
                    return ResultStatus.VIOLATION
                elif value > limit * 0.9:  # Warning at 90% of limit
                    return ResultStatus.WARNING
                else:
                    return ResultStatus.NORMAL
                    
            elif analysis_type == AnalysisType.VOLTAGE:
                # For voltage analysis, check both high and low limits
                deviation = abs(value - 1.0)  # Assuming 1.0 pu is nominal
                limit_deviation = abs(limit - 1.0)
                
                if deviation > limit_deviation:
                    return ResultStatus.VIOLATION
                elif deviation > limit_deviation * 0.9:
                    return ResultStatus.WARNING
                else:
                    return ResultStatus.NORMAL
            
            return ResultStatus.NORMAL
            
        except Exception as e:
            self.logger.error(f"Error determining result status: {e}")
            return ResultStatus.ERROR
    
    def create_analysis_result(
        self,
        element: NetworkElement,
        value: float,
        limit: float,
        contingency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Create an analysis result object.
        
        Args:
            element: Network element
            value: Measured value
            limit: Applicable limit
            contingency: Contingency scenario
            metadata: Additional metadata
            
        Returns:
            Analysis result object
        """
        status = self.determine_result_status(value, limit, self.get_analysis_type())
        
        return AnalysisResult(
            timestamp=datetime.now(),
            element=element,
            analysis_type=self.get_analysis_type(),
            value=value,
            limit=limit,
            status=status,
            contingency=contingency,
            metadata=metadata or {}
        )
    
    def filter_by_region(self, elements: List[NetworkElement], region: Region) -> List[NetworkElement]:
        """
        Filter elements by region.
        
        Args:
            elements: List of network elements
            region: Target region
            
        Returns:
            Filtered list of elements
        """
        return [element for element in elements if element.region == region]
    
    def filter_by_voltage_level(self, elements: List[NetworkElement], voltage_level: float) -> List[NetworkElement]:
        """
        Filter elements by voltage level.
        
        Args:
            elements: List of network elements
            voltage_level: Target voltage level in kV
            
        Returns:
            Filtered list of elements
        """
        return [element for element in elements if element.voltage_level == voltage_level]
    
    def filter_by_element_type(self, elements: List[NetworkElement], element_type: ElementType) -> List[NetworkElement]:
        """
        Filter elements by type.
        
        Args:
            elements: List of network elements
            element_type: Target element type
            
        Returns:
            Filtered list of elements
        """
        return [element for element in elements if element.element_type == element_type]
    
    def get_violations(self, results: List[AnalysisResult]) -> List[AnalysisResult]:
        """
        Extract violations from analysis results.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of violation results
        """
        return [result for result in results if result.is_violation]
    
    def get_summary_statistics(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Calculate summary statistics for analysis results.
        
        Args:
            results: List of analysis results
            
        Returns:
            Dictionary with summary statistics
        """
        if not results:
            return {}
        
        violations = self.get_violations(results)
        values = [result.value for result in results]
        
        return {
            'total_elements': len(results),
            'violations': len(violations),
            'violation_rate': len(violations) / len(results) * 100,
            'max_value': max(values),
            'min_value': min(values),
            'avg_value': sum(values) / len(values),
            'analysis_type': self.get_analysis_type().value
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate analyzer configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Check if PowerFactory interface is connected
            if not self.pf_interface.is_connected:
                self.logger.error("PowerFactory interface not connected")
                return False
            
            # Check if required config sections exist
            if not self.config:
                self.logger.error("No configuration provided")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
