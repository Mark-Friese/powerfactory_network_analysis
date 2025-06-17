"""
Violation data model for analysis violations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from .network_element import NetworkElement, ElementType, Region
from .analysis_result import AnalysisResult, AnalysisType, ResultStatus


# Removed ViolationType and SeverityLevel enums as they're now handled with strings


@dataclass
class Violation:
    """
    Represents a network violation found during analysis.
    
    Attributes:
        element_name: Name of element with violation
        element_type: Type of network element
        voltage_level: Voltage level of element
        region: Network region
        analysis_type: Type of analysis that found violation
        violation_value: Measured value causing violation
        limit_value: Limit that was exceeded
        severity: Severity level
        scenario: Scenario causing violation (base case or contingency)
        timestamp: When violation was detected
        metadata: Additional violation information
    """
    element_name: str
    element_type: ElementType
    voltage_level: float
    region: Region
    analysis_type: AnalysisType
    violation_value: float
    limit_value: float
    severity: str
    scenario: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Initialize metadata dictionary if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def from_analysis_result(cls, result: AnalysisResult) -> Optional['Violation']:
        """
        Create a Violation from an AnalysisResult if it represents a violation.
        
        Args:
            result: AnalysisResult to convert
            
        Returns:
            Violation object or None if result is not a violation
        """
        if result.status != ResultStatus.VIOLATION:
            return None
        
        # Determine severity based on deviation
        severity = cls._calculate_severity(result.deviation_percent)
        
        return cls(
            element_name=result.element.name,
            element_type=result.element.element_type,
            voltage_level=result.element.voltage_level,
            region=result.element.region,
            analysis_type=result.analysis_type,
            violation_value=result.value,
            limit_value=result.limit,
            severity=severity,
            scenario=result.contingency or "base_case",
            timestamp=result.timestamp,
            metadata=result.metadata.copy() if result.metadata else {}
        )
    
    @staticmethod
    def _calculate_severity(deviation_percent: float) -> str:
        """
        Calculate severity level based on percentage deviation.
        
        Args:
            deviation_percent: Percentage deviation from limit
            
        Returns:
            Appropriate severity level
        """
        abs_deviation = abs(deviation_percent)
        
        if abs_deviation < 5:
            return "Low"
        elif abs_deviation < 15:
            return "Medium"
        elif abs_deviation < 30:
            return "High"
        else:
            return "Critical"
    
    @property
    def deviation_percent(self) -> float:
        """Calculate percentage deviation from limit."""
        if self.limit_value == 0:
            return 0.0
        return ((self.violation_value - self.limit_value) / self.limit_value) * 100
    
    @property
    def is_base_case(self) -> bool:
        """Check if violation occurred in base case."""
        return self.scenario == "base_case"
    
    @property
    def priority_score(self) -> float:
        """
        Calculate priority score for violation ranking.
        Higher scores indicate higher priority violations.
        """
        severity_weights = {
            "Low": 1.0,
            "Medium": 2.0,
            "High": 3.0,
            "Critical": 4.0
        }
        
        base_score = severity_weights.get(self.severity, 2.0)
        
        # Base case violations have higher priority
        if self.is_base_case:
            base_score *= 1.5
        
        # Higher voltage levels have higher priority
        voltage_factor = min(self.voltage_level / 100.0, 2.0)
        
        return base_score * voltage_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary format."""
        return {
            'element_name': self.element_name,
            'element_type': self.element_type.value,
            'voltage_level': self.voltage_level,
            'analysis_type': self.analysis_type.value,
            'severity': self.severity,
            'violation_value': self.violation_value,
            'limit_value': self.limit_value,
            'deviation_percent': self.deviation_percent,
            'scenario': self.scenario,
            'region': self.region.value,
            'timestamp': self.timestamp.isoformat(),
            'priority_score': self.priority_score,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """String representation."""
        return (f"{self.analysis_type.value.upper()}: {self.element_name} "
                f"({self.violation_value:.3f} vs limit {self.limit_value:.3f}) "
                f"- {self.severity} severity")
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Violation(element='{self.element_name}', "
                f"type={self.analysis_type.value}, "
                f"severity={self.severity}, "
                f"scenario='{self.scenario}')")
