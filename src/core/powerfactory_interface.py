"""
PowerFactory interface module for managing PowerFactory application connections.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    import powerfactory as pf
    POWERFACTORY_AVAILABLE = True
except ImportError:
    POWERFACTORY_AVAILABLE = False
    pf = None

from ..utils.logger import get_logger


class PowerFactoryInterface:
    """
    Singleton interface for PowerFactory application management.
    
    Provides centralized access to PowerFactory API with connection management,
    error handling, and abstraction of common operations.
    """
    
    _instance: Optional['PowerFactoryInterface'] = None
    _app: Optional[Any] = None
    
    def __new__(cls) -> 'PowerFactoryInterface':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize PowerFactory interface."""
        if not hasattr(self, '_initialized'):
            self.logger = get_logger(__name__)
            self._initialized = True
            self._connected = False
            
            if not POWERFACTORY_AVAILABLE:
                self.logger.error("PowerFactory module not available")
                raise ImportError("PowerFactory module not found")
    
    def connect(self) -> bool:
        """
        Connect to PowerFactory application.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self._connected:
                self._app = pf.GetApplication()
                if self._app is None:
                    # Try alternative connection method
                    try:
                        self._app = pf.GetApplicationExt()
                    except:
                        pass
                    
                    if self._app is None:
                        self.logger.error("Failed to get PowerFactory application. Ensure PowerFactory is running.")
                        return False
                
                # Clear output window safely
                try:
                    self._app.ClearOutputWindow()
                except Exception as e:
                    self.logger.debug(f"Could not clear output window: {e}")
                
                self._connected = True
                self.logger.info("Connected to PowerFactory successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to PowerFactory: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from PowerFactory application."""
        self._app = None
        self._connected = False
        self.logger.info("Disconnected from PowerFactory")
    
    @property
    def app(self) -> Optional[Any]:
        """Get PowerFactory application object."""
        if not self._connected:
            self.connect()
        return self._app
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to PowerFactory."""
        return self._connected and self._app is not None
    
    def get_active_study_case(self) -> Optional[Any]:
        """
        Get the active study case.
        
        Returns:
            Active study case object or None if not available
        """
        try:
            if self.app:
                study_case = self.app.GetActiveStudyCase()
                if study_case is None:
                    self.logger.warning("No active study case found")
                return study_case
        except Exception as e:
            self.logger.error(f"Error getting active study case: {e}")
        return None
    
    def get_calc_relevant_objects(self, filter_str: str) -> List[Any]:
        """
        Get calculation relevant objects matching filter.
        
        Args:
            filter_str: PowerFactory filter string (e.g., '*.ElmLne')
            
        Returns:
            List of matching objects
        """
        try:
            if self.app:
                objects = self.app.GetCalcRelevantObjects(filter_str)
                return objects if objects else []
        except Exception as e:
            self.logger.error(f"Error getting objects with filter '{filter_str}': {e}")
        return []
    
    def get_from_study_case(self, class_name: str) -> Optional[Any]:
        """
        Get or create command object from study case.
        
        Args:
            class_name: PowerFactory class name (e.g., 'ComLdf')
            
        Returns:
            Command object or None if not available
        """
        try:
            if self.app:
                return self.app.GetFromStudyCase(class_name)
        except Exception as e:
            self.logger.error(f"Error getting {class_name} from study case: {e}")
        return None
    
    def execute_load_flow(self) -> bool:
        """
        Execute load flow calculation.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            ldf = self.get_from_study_case('ComLdf')
            if ldf:
                error_code = ldf.Execute()
                if error_code == 0:
                    self.logger.debug("Load flow executed successfully")
                    return True
                else:
                    self.logger.error(f"Load flow failed with error code: {error_code}")
            return False
        except Exception as e:
            self.logger.error(f"Error executing load flow: {e}")
            return False
    
    def get_project_folder(self, folder_type: str) -> Optional[Any]:
        """
        Get project folder by type.
        
        Args:
            folder_type: Folder type string (e.g., 'netmod', 'equip')
            
        Returns:
            Project folder object or None if not found
        """
        try:
            if self.app:
                return self.app.GetProjectFolder(folder_type)
        except Exception as e:
            self.logger.error(f"Error getting project folder '{folder_type}': {e}")
        return None
    
    def get_element_attribute(self, element: Any, attribute: str) -> Optional[Any]:
        """
        Safely get attribute from PowerFactory element.
        
        Args:
            element: PowerFactory element object
            attribute: Attribute name
            
        Returns:
            Attribute value or None if not available
        """
        try:
            if element and hasattr(element, 'GetAttribute'):
                return element.GetAttribute(attribute)
        except Exception as e:
            self.logger.debug(f"Error getting attribute '{attribute}': {e}")
        return None
    
    def set_element_attribute(self, element: Any, attribute: str, value: Any) -> bool:
        """
        Safely set attribute on PowerFactory element.
        
        Args:
            element: PowerFactory element object
            attribute: Attribute name
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if element and hasattr(element, 'SetAttribute'):
                element.SetAttribute(attribute, value)
                return True
        except Exception as e:
            self.logger.debug(f"Error setting attribute '{attribute}': {e}")
        return False
    
    def validate_connection(self) -> bool:
        """
        Validate PowerFactory connection and basic functionality.
        
        Returns:
            True if connection is valid and functional
        """
        try:
            if not self.is_connected:
                return False
            
            # Test basic operations
            study_case = self.get_active_study_case()
            if study_case is None:
                self.logger.warning("No active study case - connection may not be fully functional")
                return False
            
            # Test object retrieval
            test_objects = self.get_calc_relevant_objects('*')
            if not test_objects:
                self.logger.warning("No calculation relevant objects found")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            return False
    
    def get_network_statistics(self) -> Dict[str, int]:
        """
        Get basic network statistics.
        
        Returns:
            Dictionary with counts of different element types
        """
        stats = {
            'lines': 0,
            'transformers': 0,
            'busbars': 0,
            'loads': 0,
            'generators': 0
        }
        
        try:
            stats['lines'] = len(self.get_calc_relevant_objects('*.ElmLne'))
            stats['transformers'] = len(self.get_calc_relevant_objects('*.ElmTr2'))
            stats['busbars'] = len(self.get_calc_relevant_objects('*.ElmTerm'))
            stats['loads'] = len(self.get_calc_relevant_objects('*.ElmLod'))
            stats['generators'] = len(self.get_calc_relevant_objects('*.ElmSym'))
        except Exception as e:
            self.logger.error(f"Error getting network statistics: {e}")
        
        return stats
