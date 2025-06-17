"""
Analysis result data model.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from .network_element import NetworkElement


class AnalysisType(Enum):
    """Types of analysis performed."""
    THERMAL = "thermal"
    VOLTAGE = "voltage"
    BASE_CASE = "base_case"
    CONTINGENCY = "contingency"


class ResultStatus(Enum):
    """Analysis result status."""
    NORMAL = "normal"
    WARNING = "warning"
    VIOLATION = "violation"
    ERROR = "error"


@dataclass
class AnalysisResult:
    """
    Represents the result of a network analysis.
    
    Attributes:
        timestamp: When the analysis was performed
        element: Network element analyzed
        analysis_type: Type of analysis performed
        value: Measured value
        limit: Applicable limit for comparison
        status: Result status (normal, warning, violation, error)
        contingency: Contingency scenario (if applicable)
        metadata: Additional result information
    """
    timestamp: datetime
    element: NetworkElement
    analysis_type: AnalysisType
    value: float
    limit: float
    status: ResultStatus
    contingency: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Initialize metadata dictionary if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_violation(self) -> bool:
        """Check if result represents a violation."""
        return self.status == ResultStatus.VIOLATION
    
    @property
    def is_base_case(self) -> bool:
        """Check if result is from base case analysis."""
        return self.contingency is None or self.contingency == "base_case"
    
    @property
    def deviation_percent(self) -> float:
        """Calculate percentage deviation from limit."""
        if self.limit == 0:
            return 0.0
        return ((self.value - self.limit) / self.limit) * 100
    
    @property
    def severity_score(self) -> float:
        """Calculate severity score based on deviation."""
        deviation = abs(self.deviation_percent)
        if deviation <= 5:
            return 1.0  # Low
        elif deviation <= 15:
            return 2.0  # Medium
        else:
            return 3.0  # High
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'element_name': self.element.name,
            'element_type': self.element.element_type.value,
            'voltage_level': self.element.voltage_level,
            'region': self.element.region.value,
            'analysis_type': self.analysis_type.value,
            'value': self.value,
            'limit': self.limit,
            'status': self.status.value,
            'contingency': self.contingency,
            'deviation_percent': self.deviation_percent,
            'severity_score': self.severity_score,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], element: NetworkElement) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary data."""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            element=element,
            analysis_type=AnalysisType(data['analysis_type']),
            value=data['value'],
            limit=data['limit'],
            status=ResultStatus(data['status']),
            contingency=data.get('contingency'),
            metadata=data.get('metadata', {})
        )
    
    def __str__(self) -> str:
        """String representation."""
        contingency_str = f" (Contingency: {self.contingency})" if self.contingency else ""
        return (f"{self.element.name}: {self.analysis_type.value} = {self.value:.3f} "
                f"(limit: {self.limit:.3f}) - {self.status.value}{contingency_str}")
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"AnalysisResult(element='{self.element.name}', "
                f"type={self.analysis_type.value}, "
                f"value={self.value:.3f}, "
                f"status={self.status.value})")
