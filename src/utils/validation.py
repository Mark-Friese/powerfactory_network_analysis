"""
Input validation utilities for PowerFactory network analysis.
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

from ..models.network_element import ElementType, Region
from ..models.analysis_result import AnalysisType
from .logger import AnalysisLogger


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """
    Utility class for validating inputs and configurations.
    
    Provides comprehensive validation methods for different types of
    inputs used throughout the PowerFactory analysis workflow.
    """
    
    def __init__(self):
        """Initialize input validator."""
        self.logger = AnalysisLogger(self.__class__.__name__)
    
    def validate_config_structure(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration structure.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check main sections
            required_sections = ['analysis', 'regions', 'element_types']
            for section in required_sections:
                if section not in config:
                    errors.append(f"Missing required configuration section: {section}")
            
            # Validate analysis section
            if 'analysis' in config:
                analysis_errors = self._validate_analysis_config(config['analysis'])
                errors.extend(analysis_errors)
            
            # Validate regions section
            if 'regions' in config:
                regions_errors = self._validate_regions_config(config['regions'])
                errors.extend(regions_errors)
            
            # Validate element_types section
            if 'element_types' in config:
                elements_errors = self._validate_element_types_config(config['element_types'])
                errors.extend(elements_errors)
            
        except Exception as e:
            errors.append(f"Unexpected error during config validation: {e}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_analysis_config(self, analysis_config: Dict[str, Any]) -> List[str]:
        """Validate analysis configuration section."""
        errors = []
        
        # Check thermal limits
        if 'thermal_limits' in analysis_config:
            thermal_limits = analysis_config['thermal_limits']
            
            if not isinstance(thermal_limits, dict):
                errors.append("thermal_limits must be a dictionary")
            else:
                # Validate thermal limit values
                for limit_type, value in thermal_limits.items():
                    if not isinstance(value, (int, float)):
                        errors.append(f"thermal_limits.{limit_type} must be numeric")
                    elif value <= 0 or value > 200:
                        errors.append(f"thermal_limits.{limit_type} must be between 0 and 200")
        
        # Check voltage limits
        if 'voltage_limits' in analysis_config:
            voltage_limits = analysis_config['voltage_limits']
            
            if not isinstance(voltage_limits, dict):
                errors.append("voltage_limits must be a dictionary")
            else:
                for region_name, region_limits in voltage_limits.items():
                    if region_name not in ['scotland', 'england']:
                        errors.append(f"Unknown region in voltage_limits: {region_name}")
                    
                    if not isinstance(region_limits, dict):
                        errors.append(f"voltage_limits.{region_name} must be a dictionary")
                        continue
                    
                    # Validate voltage level limits
                    for voltage_level, limits in region_limits.items():
                        try:
                            float(voltage_level)  # Should be convertible to float
                        except ValueError:
                            errors.append(f"Invalid voltage level in {region_name}: {voltage_level}")
                        
                        if not isinstance(limits, dict):
                            errors.append(f"Limits for {region_name}.{voltage_level} must be a dictionary")
                            continue
                        
                        if 'min' not in limits or 'max' not in limits:
                            errors.append(f"Missing min/max limits for {region_name}.{voltage_level}")
                            continue
                        
                        min_limit = limits['min']
                        max_limit = limits['max']
                        
                        if not isinstance(min_limit, (int, float)) or not isinstance(max_limit, (int, float)):
                            errors.append(f"Voltage limits for {region_name}.{voltage_level} must be numeric")
                        elif min_limit >= max_limit:
                            errors.append(f"Min limit >= max limit for {region_name}.{voltage_level}")
                        elif min_limit <= 0 or max_limit <= 0:
                            errors.append(f"Voltage limits must be positive for {region_name}.{voltage_level}")
        
        # Check options
        if 'options' in analysis_config:
            options = analysis_config['options']
            
            if not isinstance(options, dict):
                errors.append("options must be a dictionary")
            else:
                boolean_options = ['run_base_case', 'run_contingency', 'include_out_of_service']
                for option in boolean_options:
                    if option in options and not isinstance(options[option], bool):
                        errors.append(f"options.{option} must be boolean")
                
                if 'max_contingencies' in options:
                    max_cont = options['max_contingencies']
                    if not isinstance(max_cont, int) or max_cont <= 0:
                        errors.append("options.max_contingencies must be positive integer")
        
        return errors
    
    def _validate_regions_config(self, regions_config: Dict[str, Any]) -> List[str]:
        """Validate regions configuration section."""
        errors = []
        
        required_regions = ['scotland', 'england']
        for region in required_regions:
            if region not in regions_config:
                errors.append(f"Missing required region: {region}")
                continue
            
            region_config = regions_config[region]
            
            if not isinstance(region_config, dict):
                errors.append(f"Region {region} config must be a dictionary")
                continue
            
            # Check required fields
            required_fields = ['name', 'code', 'voltage_levels']
            for field in required_fields:
                if field not in region_config:
                    errors.append(f"Missing required field {field} in region {region}")
            
            # Validate voltage levels
            if 'voltage_levels' in region_config:
                voltage_levels = region_config['voltage_levels']
                if not isinstance(voltage_levels, list):
                    errors.append(f"voltage_levels for {region} must be a list")
                else:
                    for level in voltage_levels:
                        if not isinstance(level, (int, float)) or level <= 0:
                            errors.append(f"Invalid voltage level in {region}: {level}")
        
        return errors
    
    def _validate_element_types_config(self, element_types_config: Dict[str, Any]) -> List[str]:
        """Validate element types configuration section."""
        errors = []
        
        required_categories = ['thermal_elements', 'voltage_elements']
        for category in required_categories:
            if category not in element_types_config:
                errors.append(f"Missing required element category: {category}")
                continue
            
            elements = element_types_config[category]
            if not isinstance(elements, list):
                errors.append(f"{category} must be a list")
                continue
            
            # Validate PowerFactory class names
            valid_pf_classes = ['ElmLne', 'ElmTr2', 'ElmTr3', 'ElmCoup', 'ElmTerm', 'ElmLod', 'ElmSym']
            for element_class in elements:
                if element_class not in valid_pf_classes:
                    errors.append(f"Unknown PowerFactory class in {category}: {element_class}")
        
        return errors
    
    def validate_file_path(self, filepath: Union[str, Path], 
                          must_exist: bool = True,
                          allowed_extensions: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Validate file path.
        
        Args:
            filepath: Path to validate
            must_exist: Whether file must exist
            allowed_extensions: List of allowed file extensions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(filepath)
            
            if must_exist and not path.exists():
                return False, f"File does not exist: {filepath}"
            
            if must_exist and not path.is_file():
                return False, f"Path is not a file: {filepath}"
            
            if allowed_extensions:
                extension = path.suffix.lower()
                if extension not in [ext.lower() for ext in allowed_extensions]:
                    return False, f"File extension not allowed. Expected: {allowed_extensions}, got: {extension}"
            
            # Check if path is valid (can be created)
            if not must_exist:
                try:
                    path.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    return False, f"Cannot create directory for file: {e}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Invalid file path: {e}"
    
    def validate_directory_path(self, dirpath: Union[str, Path], 
                               must_exist: bool = True,
                               create_if_missing: bool = False) -> Tuple[bool, str]:
        """
        Validate directory path.
        
        Args:
            dirpath: Directory path to validate
            must_exist: Whether directory must exist
            create_if_missing: Create directory if it doesn't exist
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(dirpath)
            
            if must_exist and not path.exists():
                if create_if_missing:
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except OSError as e:
                        return False, f"Cannot create directory: {e}"
                else:
                    return False, f"Directory does not exist: {dirpath}"
            
            if path.exists() and not path.is_dir():
                return False, f"Path is not a directory: {dirpath}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Invalid directory path: {e}"
    
    def validate_numeric_range(self, value: Union[int, float], 
                              min_value: Optional[Union[int, float]] = None,
                              max_value: Optional[Union[int, float]] = None,
                              value_name: str = "value") -> Tuple[bool, str]:
        """
        Validate numeric value is within range.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not isinstance(value, (int, float)):
                return False, f"{value_name} must be numeric, got: {type(value).__name__}"
            
            if min_value is not None and value < min_value:
                return False, f"{value_name} must be >= {min_value}, got: {value}"
            
            if max_value is not None and value > max_value:
                return False, f"{value_name} must be <= {max_value}, got: {value}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating {value_name}: {e}"
    
    def validate_string_format(self, value: str, 
                              pattern: Optional[str] = None,
                              min_length: Optional[int] = None,
                              max_length: Optional[int] = None,
                              value_name: str = "string") -> Tuple[bool, str]:
        """
        Validate string format.
        
        Args:
            value: String to validate
            pattern: Regex pattern to match
            min_length: Minimum string length
            max_length: Maximum string length
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not isinstance(value, str):
                return False, f"{value_name} must be string, got: {type(value).__name__}"
            
            if min_length is not None and len(value) < min_length:
                return False, f"{value_name} must be at least {min_length} characters"
            
            if max_length is not None and len(value) > max_length:
                return False, f"{value_name} must be at most {max_length} characters"
            
            if pattern is not None:
                if not re.match(pattern, value):
                    return False, f"{value_name} does not match required pattern: {pattern}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validating {value_name}: {e}"
    
    def validate_enum_value(self, value: Any, 
                           enum_class: type,
                           value_name: str = "value") -> Tuple[bool, str]:
        """
        Validate value against enum.
        
        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if hasattr(enum_class, '__members__'):
                # Standard enum
                valid_values = list(enum_class.__members__.keys())
                if isinstance(value, enum_class):
                    return True, ""
                elif isinstance(value, str) and value in valid_values:
                    return True, ""
                else:
                    return False, f"{value_name} must be one of: {valid_values}, got: {value}"
            else:
                return False, f"Invalid enum class provided: {enum_class}"
            
        except Exception as e:
            return False, f"Error validating {value_name} against enum: {e}"
    
    def validate_list_content(self, values: List[Any], 
                             item_validator: callable,
                             list_name: str = "list") -> Tuple[bool, List[str]]:
        """
        Validate list content using item validator.
        
        Args:
            values: List to validate
            item_validator: Function to validate individual items
            list_name: Name of list for error messages
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            if not isinstance(values, list):
                errors.append(f"{list_name} must be a list, got: {type(values).__name__}")
                return False, errors
            
            for i, item in enumerate(values):
                try:
                    is_valid, error_msg = item_validator(item)
                    if not is_valid:
                        errors.append(f"{list_name}[{i}]: {error_msg}")
                except Exception as e:
                    errors.append(f"{list_name}[{i}]: Validation error: {e}")
            
        except Exception as e:
            errors.append(f"Error validating {list_name}: {e}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_datetime_string(self, datetime_str: str, 
                                format_str: str = "%Y-%m-%d %H:%M:%S",
                                value_name: str = "datetime") -> Tuple[bool, str]:
        """
        Validate datetime string format.
        
        Args:
            datetime_str: Datetime string to validate
            format_str: Expected datetime format
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            datetime.strptime(datetime_str, format_str)
            return True, ""
            
        except ValueError as e:
            return False, f"{value_name} invalid format. Expected: {format_str}, error: {e}"
        except Exception as e:
            return False, f"Error validating {value_name}: {e}"
    
    def validate_percentage(self, value: Union[int, float], 
                           value_name: str = "percentage") -> Tuple[bool, str]:
        """
        Validate percentage value (0-100).
        
        Args:
            value: Percentage value to validate
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validate_numeric_range(value, 0, 100, value_name)
    
    def validate_per_unit(self, value: Union[int, float], 
                         value_name: str = "per unit value") -> Tuple[bool, str]:
        """
        Validate per unit value (typically 0-2).
        
        Args:
            value: Per unit value to validate
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validate_numeric_range(value, 0, 2, value_name)
    
    def validate_voltage_level(self, value: Union[int, float], 
                              value_name: str = "voltage level") -> Tuple[bool, str]:
        """
        Validate voltage level (kV).
        
        Args:
            value: Voltage level to validate
            value_name: Name of value for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Common UK voltage levels
        valid_levels = [0.4, 11, 33, 132, 275, 400]
        
        if not isinstance(value, (int, float)):
            return False, f"{value_name} must be numeric"
        
        if value not in valid_levels:
            self.logger.warning(f"Unusual voltage level: {value}kV")
        
        return self.validate_numeric_range(value, 0.1, 1000, value_name)
    
    def create_validation_report(self, validation_results: List[Tuple[str, bool, str]]) -> Dict[str, Any]:
        """
        Create validation report from multiple validation results.
        
        Args:
            validation_results: List of (item_name, is_valid, error_message) tuples
            
        Returns:
            Validation report dictionary
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_items': len(validation_results),
            'valid_items': 0,
            'invalid_items': 0,
            'errors': [],
            'warnings': [],
            'is_valid': True
        }
        
        for item_name, is_valid, message in validation_results:
            if is_valid:
                report['valid_items'] += 1
            else:
                report['invalid_items'] += 1
                report['errors'].append(f"{item_name}: {message}")
                report['is_valid'] = False
        
        report['success_rate'] = (report['valid_items'] / report['total_items'] * 100) if report['total_items'] > 0 else 0
        
        return report
