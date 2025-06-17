"""
Network element data model for PowerFactory objects.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict
from enum import Enum


class ElementType(Enum):
    """Network element types."""
    LINE = "ElmLne"
    TRANSFORMER_2W = "ElmTr2"
    TRANSFORMER_3W = "ElmTr3"
    BUSBAR = "ElmTerm"
    COUPLER = "ElmCoup"
    LOAD = "ElmLod"
    GENERATOR = "ElmSym"


class Region(Enum):
    """Network regions."""
    SCOTLAND = "scotland"
    ENGLAND = "england"


@dataclass
class NetworkElement:
    """
    Represents a network element in PowerFactory.
    
    Attributes:
        name: Element name/identifier
        element_type: PowerFactory class type
        voltage_level: Nominal voltage level in kV
        region: Network region (Scotland/England)
        powerfactory_object: Reference to actual PowerFactory object
        operational_status: Whether element is in service
        properties: Additional element properties
    """
    name: str
    element_type: ElementType
    voltage_level: float
    region: Region
    powerfactory_object: Any
    operational_status: bool = True
    properties: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        """Initialize properties dictionary if not provided."""
        if self.properties is None:
            self.properties = {}
    
    @property
    def is_thermal_element(self) -> bool:
        """Check if element is subject to thermal analysis."""
        thermal_types = {
            ElementType.LINE,
            ElementType.TRANSFORMER_2W,
            ElementType.TRANSFORMER_3W,
            ElementType.COUPLER
        }
        return self.element_type in thermal_types
    
    @property
    def is_voltage_element(self) -> bool:
        """Check if element is subject to voltage analysis."""
        return self.element_type == ElementType.BUSBAR
    
    def get_powerfactory_attribute(self, attribute: str) -> Any:
        """
        Get attribute value from PowerFactory object.
        
        Args:
            attribute: PowerFactory attribute name
            
        Returns:
            Attribute value or None if not available
        """
        try:
            if self.powerfactory_object:
                return self.powerfactory_object.GetAttribute(attribute)
        except Exception:
            pass
        return None
    
    def set_out_of_service(self, status: bool) -> bool:
        """
        Set element out of service status.
        
        Args:
            status: True for out of service, False for in service
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.powerfactory_object:
                self.powerfactory_object.outserv = 1 if status else 0
                self.operational_status = not status
                return True
        except Exception:
            pass
        return False
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} ({self.element_type.value}) - {self.voltage_level}kV"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"NetworkElement(name='{self.name}', "
                f"type={self.element_type.value}, "
                f"voltage={self.voltage_level}kV, "
                f"region={self.region.value})")
