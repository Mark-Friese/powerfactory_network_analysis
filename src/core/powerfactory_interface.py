"""
PowerFactory interface module for managing PowerFactory application connections.
"""

import os
import logging
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

# PowerFactory path detection and configuration
def _configure_powerfactory_path():
    """Configure PowerFactory path and return version info."""
    base_path = r"C:\Program Files\DIgSILENT"
    
    # List of known PowerFactory versions (newest first)
    known_versions = [
        "PowerFactory 2025",
        "PowerFactory 2024 SP4",
        "PowerFactory 2024 SP3", 
        "PowerFactory 2024 SP2",
        "PowerFactory 2024 SP1",
        "PowerFactory 2024",
        "PowerFactory 2023 SP6",
        "PowerFactory 2023 SP5",
        "PowerFactory 2023 SP4",
        "PowerFactory 2023 SP3",
        "PowerFactory 2023 SP2",
        "PowerFactory 2023 SP1",
        "PowerFactory 2023",
        "PowerFactory 2022 SP6",
        "PowerFactory 2022 SP5",
        "PowerFactory 2022 SP4"
    ]
    
    # Check if base DIgSILENT directory exists
    if not os.path.exists(base_path):
        return None, "DIgSILENT installation directory not found"
    
    # Find the first available PowerFactory version
    for version in known_versions:
        version_path = os.path.join(base_path, version)
        if os.path.exists(version_path):
            # Add to PATH for DLL loading
            if version_path not in os.environ.get("PATH", ""):
                os.environ["PATH"] = version_path + ";" + os.environ.get("PATH", "")
            
            # Also add to Python path if needed
            if version_path not in sys.path:
                sys.path.insert(0, version_path)
                
            return version_path, version
    
    # If no standard version found, try to find any PowerFactory directory
    try:
        for item in os.listdir(base_path):
            if "PowerFactory" in item and os.path.isdir(os.path.join(base_path, item)):
                version_path = os.path.join(base_path, item)
                if version_path not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = version_path + ";" + os.environ.get("PATH", "")
                if version_path not in sys.path:
                    sys.path.insert(0, version_path)
                return version_path, item
    except OSError:
        pass
    
    return None, "No PowerFactory installation found"

# Configure PowerFactory path before importing
POWERFACTORY_PATH, POWERFACTORY_VERSION = _configure_powerfactory_path()

# Try to import PowerFactory module
try:
    import powerfactory as pf
    POWERFACTORY_AVAILABLE = True
    if POWERFACTORY_VERSION and "PowerFactory" in POWERFACTORY_VERSION:
        POWERFACTORY_VERSION = POWERFACTORY_VERSION.replace("PowerFactory ", "")
    else:
        POWERFACTORY_VERSION = "Unknown Version"
except ImportError as e:
    POWERFACTORY_AVAILABLE = False
    pf = None
    POWERFACTORY_VERSION = f"Not Available ({str(e)})"

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
            self._user_id: Optional[str] = None
            
            # Log PowerFactory version information
            self.logger.info(f"PowerFactory Interface initialized for version: {POWERFACTORY_VERSION}")
            if POWERFACTORY_AVAILABLE:
                self.logger.info(f"PowerFactory path configured: {POWERFACTORY_PATH}")
            else:
                self.logger.error(f"PowerFactory module not available: {POWERFACTORY_VERSION}")
                # Don't raise exception here - allow for mock/testing scenarios
                self.logger.warning("PowerFactory operations will not be available")
    
    @property
    def is_available(self) -> bool:
        """Check if PowerFactory is available for use."""
        return POWERFACTORY_AVAILABLE
    
    def connect(self, user_id: Optional[str] = None) -> bool:
        """
        Connect to PowerFactory application.
        
        Args:
            user_id: PowerFactory user ID for login (optional)
        
        Returns:
            True if connection successful, False otherwise
        """
        if not POWERFACTORY_AVAILABLE:
            self.logger.error("Cannot connect: PowerFactory module not available")
            return False
        
        try:
            if not self._connected:
                # Store user ID for tracking
                if user_id:
                    self._user_id = user_id
                
                # Try connection with user authentication first (recommended approach)
                if user_id:
                    try:
                        self.logger.info(f"Attempting connection with user authentication: {user_id}")
                        self._app = pf.GetApplicationExt(user_id)
                        if self._app is not None:
                            self.logger.info(f"Connected to PowerFactory with user authentication: {user_id}")
                        else:
                            self.logger.error(f"Failed to authenticate user: {user_id}")
                            return False
                    except Exception as e:
                        self.logger.error(f"Authentication failed for user {user_id}: {e}")
                        return False
                else:
                    # Try without authentication
                    self.logger.info("Attempting connection without user authentication")
                    self._app = pf.GetApplication()
                    if self._app is None:
                        # Try alternative connection method
                        try:
                            self._app = pf.GetApplicationExt()
                        except Exception as e:
                            self.logger.debug(f"Alternative connection method failed: {e}")
                        
                        if self._app is None:
                            self.logger.error("Failed to get PowerFactory application. Ensure PowerFactory is running.")
                            return False
                    
                    self.logger.info("Connected to PowerFactory without user authentication")
                
                # Clear output window safely
                try:
                    self._app.ClearOutputWindow()
                except Exception as e:
                    self.logger.debug(f"Could not clear output window: {e}")
                
                self._connected = True
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to PowerFactory: {e}")
            return False

    def set_user_id(self, user_id: str) -> None:
        """
        Set the user ID for future connections.
        
        Args:
            user_id: PowerFactory user ID
        """
        self._user_id = user_id
        self.logger.info(f"User ID set to: {user_id}")

    def get_current_user(self) -> Optional[str]:
        """
        Get the current logged-in user ID.
        
        Returns:
            Current user ID or None if not set
        """
        return self._user_id

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
            test_objects = self.get_calc_relevant_objects('*.ElmTerm')
            self.logger.debug(f"Found {len(test_objects)} terminal objects during validation")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            return False
    
    def get_network_statistics(self) -> Dict[str, int]:
        """
        Get basic network statistics for validation.
        
        Returns:
            Dictionary with counts of major element types
        """
        stats = {
            'lines': 0,
            'transformers': 0,
            'terminals': 0,
            'loads': 0,
            'generators': 0
        }
        
        try:
            if self.is_connected:
                stats['lines'] = len(self.get_calc_relevant_objects('*.ElmLne'))
                stats['transformers'] = len(self.get_calc_relevant_objects('*.ElmTr*'))
                stats['terminals'] = len(self.get_calc_relevant_objects('*.ElmTerm'))
                stats['loads'] = len(self.get_calc_relevant_objects('*.ElmLod'))
                stats['generators'] = len(self.get_calc_relevant_objects('*.ElmSym'))
                
        except Exception as e:
            self.logger.error(f"Error getting network statistics: {e}")
        
        return stats
