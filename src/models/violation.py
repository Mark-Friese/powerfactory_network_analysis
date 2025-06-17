"""
Violation data model for analysis violations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from .network_element import NetworkElement
from .analysis_result import AnalysisResult, AnalysisType, ResultStatus


class ViolationType(Enum):
    """Types of violations."""
    THERMAL_OVERLOAD = "thermal_overload"
    VOLTAGE_HIGH = "voltage_high"
    VOLTAGE_LOW = "voltage_low"
    POWER_FLOW = "power_flow"


class SeverityLevel(Enum):
    """Violation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Violation:
    """
    Represents a network violation found during analysis.
    
    Attributes:
        element: Network element with violation
        violation_type: Type of violation
        severity: Severity level
        value: Measured value causing violation
        limit: Limit that was exceeded
        contingency: Contingency scenario causing violation
        region: Network region
        timestamp: When violation was detected
        metadata: Additional violation information
    """
    element: NetworkElement
    violation_type: ViolationType
    severity: SeverityLevel
    value: float
    limit: float
    contingency: str
    region: str
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
        
        # Determine violation type
        if result.analysis_type == AnalysisType.THERMAL:
            violation_type = ViolationType.THERMAL_OVERLOAD
        elif result.analysis_type == AnalysisType.VOLTAGE:
            if result.value > result.limit:
                violation_type = ViolationType.VOLTAGE_HIGH
            else:
                violation_type = ViolationType.VOLTAGE_LOW
        else:
            return None
        
        # Determine severity based on deviation
        severity = cls._calculate_severity(result.deviation_percent)
        
        return cls(
            element=result.element,
            violation_type=violation_type,
            severity=severity,
            value=result.value,
            limit=result.limit,
            contingency=result.contingency or "base_case",
            region=result.element.region.value,
            timestamp=result.timestamp,
            metadata=result.metadata.copy() if result.metadata else {}
        )
    
    @staticmethod
    def _calculate_severity(deviation_percent: float) -> SeverityLevel:
        """
        Calculate severity level based on percentage deviation.
        
        Args:
            deviation_percent: Percentage deviation from limit
            
        Returns:
            Appropriate severity level
        """
        abs_deviation = abs(deviation_percent)
        
        if abs_deviation < 5:
            return SeverityLevel.LOW
        elif abs_deviation < 15:
            return SeverityLevel.MEDIUM
        elif abs_deviation < 30:
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.CRITICAL
    
    @property
    def deviation_percent(self) -> float:
        """Calculate percentage deviation from limit."""
        if self.limit == 0:
            return 0.0
        return ((self.value - self.limit) / self.limit) * 100
    
    @property
    def is_base_case(self) -> bool:
        """Check if violation occurred in base case."""
        return self.contingency == "base_case"
    
    @property
    def priority_score(self) -> float:
        """
        Calculate priority score for violation ranking.
        Higher scores indicate higher priority violations.
        """
        severity_weights = {
            SeverityLevel.LOW: 1.0,
            SeverityLevel.MEDIUM: 2.0,
            SeverityLevel.HIGH: 3.0,
            SeverityLevel.CRITICAL: 4.0
        }
        
        base_score = severity_weights[self.severity]
        
        # Base case violations have higher priority
        if self.is_base_case:
            base_score *= 1.5
        
        # Higher voltage levels have higher priority
        voltage_factor = min(self.element.voltage_level / 100.0, 2.0)
        
        return base_score * voltage_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary format."""
        return {
            'element_name': self.element.name,
            'element_type': self.element.element_type.value,
            'voltage_level': self.element.voltage_level,
            'violation_type': self.violation_type.value,
            'severity': self.severity.value,
            'value': self.value,
            'limit': self.limit,
            'deviation_percent': self.deviation_percent,
            'contingency': self.contingency,
            'region': self.region,
            'timestamp': self.timestamp.isoformat(),
            'priority_score': self.priority_score,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """String representation."""
        return (f"{self.violation_type.value.upper()}: {self.element.name} "
                f"({self.value:.3f} vs limit {self.limit:.3f}) "
                f"- {self.severity.value} severity")
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Violation(element='{self.element.name}', "
                f"type={self.violation_type.value}, "
                f"severity={self.severity.value}, "
                f"contingency='{self.contingency}')")
