"""
Tests for utility components.
"""

import sys
import tempfile
import unittest
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from src.models.network_element import ElementType
from src.utils.file_handler import FileHandler
from src.utils.validation import InputValidator


class TestUtils(unittest.TestCase):
    """Test cases for utility components."""

    def setUp(self):
        """Set up test fixtures."""
        self.file_handler = FileHandler()
        self.validator = InputValidator()

        # Create temporary directory for file operations
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil

        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)

    def test_file_handler_yaml_operations(self):
        """Test YAML file read/write operations."""
        # Test data
        test_data = {
            "test_section": {
                "string_value": "test_string",
                "numeric_value": 42,
                "list_value": [1, 2, 3],
                "boolean_value": True,
            }
        }

        yaml_file = self.temp_path / "test.yaml"

        # Test write
        result = self.file_handler.write_yaml(test_data, yaml_file)
        self.assertTrue(result)
        self.assertTrue(yaml_file.exists())

        # Test read
        loaded_data = self.file_handler.read_yaml(yaml_file)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data, test_data)

        # Test read non-existent file
        missing_file = self.temp_path / "missing.yaml"
        loaded_data = self.file_handler.read_yaml(missing_file)
        self.assertIsNone(loaded_data)

    def test_file_handler_json_operations(self):
        """Test JSON file read/write operations."""
        # Test data
        test_data = {
            "string": "test",
            "number": 123,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
        }

        json_file = self.temp_path / "test.json"

        # Test write
        result = self.file_handler.write_json(test_data, json_file)
        self.assertTrue(result)
        self.assertTrue(json_file.exists())

        # Test read
        loaded_data = self.file_handler.read_json(json_file)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data, test_data)

        # Test read non-existent file
        missing_file = self.temp_path / "missing.json"
        loaded_data = self.file_handler.read_json(missing_file)
        self.assertIsNone(loaded_data)

    def test_file_handler_csv_operations(self):
        """Test CSV file read/write operations."""
        # Test data
        test_data = [
            {"name": "Element1", "type": "Line", "voltage": 33.0},
            {"name": "Element2", "type": "Transformer", "voltage": 132.0},
            {"name": "Element3", "type": "Busbar", "voltage": 11.0},
        ]

        csv_file = self.temp_path / "test.csv"

        # Test write
        result = self.file_handler.write_csv(test_data, csv_file)
        self.assertTrue(result)
        self.assertTrue(csv_file.exists())

        # Test read
        loaded_data = self.file_handler.read_csv(csv_file)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data), 3)
        self.assertEqual(loaded_data[0]["name"], "Element1")
        self.assertEqual(loaded_data[1]["type"], "Transformer")

        # Test read non-existent file
        missing_file = self.temp_path / "missing.csv"
        loaded_data = self.file_handler.read_csv(missing_file)
        self.assertIsNone(loaded_data)

    def test_file_handler_text_operations(self):
        """Test text file read/write operations."""
        test_content = "This is a test file.\nWith multiple lines.\nAnd some content."
        text_file = self.temp_path / "test.txt"

        # Test write
        result = self.file_handler.write_text_file(test_content, text_file)
        self.assertTrue(result)
        self.assertTrue(text_file.exists())

        # Test read
        loaded_content = self.file_handler.read_text_file(text_file)
        self.assertEqual(loaded_content, test_content)

        # Test read non-existent file
        missing_file = self.temp_path / "missing.txt"
        loaded_content = self.file_handler.read_text_file(missing_file)
        self.assertIsNone(loaded_content)

    def test_file_handler_directory_operations(self):
        """Test directory operations."""
        test_dir = self.temp_path / "test_subdir" / "nested"

        # Test ensure directory
        result = self.file_handler.ensure_directory(test_dir)
        self.assertTrue(result)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())

        # Test with existing directory
        result = self.file_handler.ensure_directory(test_dir)
        self.assertTrue(result)  # Should still succeed

    def test_file_handler_file_info(self):
        """Test file information retrieval."""
        # Create test file
        test_file = self.temp_path / "info_test.txt"
        test_content = "Test content for file info"
        self.file_handler.write_text_file(test_content, test_file)

        # Get file info
        info = self.file_handler.get_file_info(test_file)

        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "info_test.txt")
        self.assertEqual(info["size_bytes"], len(test_content.encode("utf-8")))
        self.assertTrue(info["is_file"])
        self.assertFalse(info["is_directory"])
        self.assertEqual(info["extension"], ".txt")
        self.assertIn("created", info)
        self.assertIn("modified", info)

        # Test non-existent file
        missing_file = self.temp_path / "missing.txt"
        info = self.file_handler.get_file_info(missing_file)
        self.assertIsNone(info)

    def test_file_handler_backup_operations(self):
        """Test file backup operations."""
        # Create original file
        original_file = self.temp_path / "original.txt"
        original_content = "Original content"
        self.file_handler.write_text_file(original_content, original_file)

        # Create backup
        backup_path = self.file_handler.backup_file(original_file, "backup")

        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())

        # Verify backup content
        backup_content = self.file_handler.read_text_file(backup_path)
        self.assertEqual(backup_content, original_content)

        # Test backup of non-existent file
        missing_file = self.temp_path / "missing.txt"
        backup_path = self.file_handler.backup_file(missing_file)
        self.assertIsNone(backup_path)

    def test_validator_config_structure(self):
        """Test configuration structure validation."""
        # Valid configuration
        valid_config = {
            "analysis": {
                "thermal_limits": {
                    "default": 90.0,
                    "lines": 90.0,
                    "transformers": 85.0,
                },
                "voltage_limits": {"scotland": {"33.0": {"min": 0.95, "max": 1.05}}},
            },
            "regions": {
                "scotland": {
                    "name": "Scotland",
                    "code": "SCOT",
                    "voltage_levels": [33.0, 11.0],
                }
            },
            "element_types": {
                "thermal_elements": ["ElmLne", "ElmTr2"],
                "voltage_elements": ["ElmTerm"],
            },
        }

        is_valid, errors = self.validator.validate_config_structure(valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid configuration - missing required section
        invalid_config = {
            "analysis": {},
            # Missing 'regions' and 'element_types'
        }

        is_valid, errors = self.validator.validate_config_structure(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_validator_file_path_validation(self):
        """Test file path validation."""
        # Valid existing file
        test_file = self.temp_path / "test.txt"
        self.file_handler.write_text_file("test", test_file)

        is_valid, error = self.validator.validate_file_path(test_file, must_exist=True)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

        # Non-existent file when must exist
        missing_file = self.temp_path / "missing.txt"
        is_valid, error = self.validator.validate_file_path(
            missing_file, must_exist=True
        )
        self.assertFalse(is_valid)
        self.assertIn("does not exist", error)

        # File extension validation
        is_valid, error = self.validator.validate_file_path(
            test_file, must_exist=True, allowed_extensions=[".yaml", ".yml"]
        )
        self.assertFalse(is_valid)
        self.assertIn("extension not allowed", error)

        # Valid extension
        yaml_file = self.temp_path / "test.yaml"
        self.file_handler.write_text_file("test", yaml_file)
        is_valid, error = self.validator.validate_file_path(
            yaml_file, must_exist=True, allowed_extensions=[".yaml", ".yml"]
        )
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validator_numeric_range_validation(self):
        """Test numeric range validation."""
        # Valid value within range
        is_valid, error = self.validator.validate_numeric_range(
            50, 0, 100, "test_value"
        )
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

        # Value below minimum
        is_valid, error = self.validator.validate_numeric_range(
            -5, 0, 100, "test_value"
        )
        self.assertFalse(is_valid)
        self.assertIn("must be >= 0", error)

        # Value above maximum
        is_valid, error = self.validator.validate_numeric_range(
            150, 0, 100, "test_value"
        )
        self.assertFalse(is_valid)
        self.assertIn("must be <= 100", error)

        # Non-numeric value
        is_valid, error = self.validator.validate_numeric_range(
            "not_a_number", 0, 100, "test_value"
        )
        self.assertFalse(is_valid)
        self.assertIn("must be numeric", error)

    def test_validator_string_format_validation(self):
        """Test string format validation."""
        # Valid string
        is_valid, error = self.validator.validate_string_format(
            "valid_string", value_name="test"
        )
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

        # String length validation
        is_valid, error = self.validator.validate_string_format(
            "short", min_length=10, value_name="test"
        )
        self.assertFalse(is_valid)
        self.assertIn("at least 10 characters", error)

        is_valid, error = self.validator.validate_string_format(
            "very_long_string", max_length=5, value_name="test"
        )
        self.assertFalse(is_valid)
        self.assertIn("at most 5 characters", error)

        # Pattern validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        is_valid, error = self.validator.validate_string_format(
            "test@example.com", pattern=email_pattern, value_name="email"
        )
        self.assertTrue(is_valid)

        is_valid, error = self.validator.validate_string_format(
            "invalid_email", pattern=email_pattern, value_name="email"
        )
        self.assertFalse(is_valid)
        self.assertIn("does not match required pattern", error)

        # Non-string value
        is_valid, error = self.validator.validate_string_format(123, value_name="test")
        self.assertFalse(is_valid)
        self.assertIn("must be string", error)

    def test_validator_enum_validation(self):
        """Test enum value validation."""
        # Valid enum value
        is_valid, error = self.validator.validate_enum_value(
            ElementType.LINE, ElementType, "element_type"
        )
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

        # Valid string representation
        is_valid, error = self.validator.validate_enum_value(
            "LINE", ElementType, "element_type"
        )
        self.assertTrue(is_valid)

        # Invalid value
        is_valid, error = self.validator.validate_enum_value(
            "INVALID_TYPE", ElementType, "element_type"
        )
        self.assertFalse(is_valid)
        self.assertIn("must be one of", error)

    def test_validator_percentage_validation(self):
        """Test percentage value validation."""
        # Valid percentage
        is_valid, error = self.validator.validate_percentage(75.5, "loading")
        self.assertTrue(is_valid)

        # Boundary values
        is_valid, error = self.validator.validate_percentage(0, "loading")
        self.assertTrue(is_valid)

        is_valid, error = self.validator.validate_percentage(100, "loading")
        self.assertTrue(is_valid)

        # Invalid percentages
        is_valid, error = self.validator.validate_percentage(-5, "loading")
        self.assertFalse(is_valid)

        is_valid, error = self.validator.validate_percentage(150, "loading")
        self.assertFalse(is_valid)

    def test_validator_per_unit_validation(self):
        """Test per unit value validation."""
        # Valid per unit values
        is_valid, error = self.validator.validate_per_unit(1.0, "voltage")
        self.assertTrue(is_valid)

        is_valid, error = self.validator.validate_per_unit(0.95, "voltage")
        self.assertTrue(is_valid)

        is_valid, error = self.validator.validate_per_unit(1.05, "voltage")
        self.assertTrue(is_valid)

        # Invalid per unit values
        is_valid, error = self.validator.validate_per_unit(-0.1, "voltage")
        self.assertFalse(is_valid)

        is_valid, error = self.validator.validate_per_unit(3.0, "voltage")
        self.assertFalse(is_valid)

    def test_validator_voltage_level_validation(self):
        """Test voltage level validation."""
        # Common UK voltage levels
        valid_levels = [11, 33, 132, 275, 400]

        for level in valid_levels:
            is_valid, error = self.validator.validate_voltage_level(
                level, "voltage_level"
            )
            self.assertTrue(is_valid, f"Level {level}kV should be valid")

        # Invalid voltage levels
        is_valid, error = self.validator.validate_voltage_level(-10, "voltage_level")
        self.assertFalse(is_valid)

        is_valid, error = self.validator.validate_voltage_level(0, "voltage_level")
        self.assertFalse(is_valid)

    def test_validator_list_content_validation(self):
        """Test list content validation."""

        # Valid list with valid items
        def validate_positive_number(value):
            if isinstance(value, (int, float)) and value > 0:
                return True, ""
            return False, "Must be positive number"

        valid_list = [1, 2.5, 10]
        is_valid, errors = self.validator.validate_list_content(
            valid_list, validate_positive_number, "numbers"
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # List with invalid items
        invalid_list = [1, -2, "not_a_number"]
        is_valid, errors = self.validator.validate_list_content(
            invalid_list, validate_positive_number, "numbers"
        )
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

        # Non-list value
        is_valid, errors = self.validator.validate_list_content(
            "not_a_list", validate_positive_number, "numbers"
        )
        self.assertFalse(is_valid)
        self.assertIn("must be a list", errors[0])

    def test_validator_datetime_string_validation(self):
        """Test datetime string validation."""
        # Valid datetime strings
        valid_datetime = "2023-12-25 15:30:45"
        is_valid, error = self.validator.validate_datetime_string(
            valid_datetime, "%Y-%m-%d %H:%M:%S", "timestamp"
        )
        self.assertTrue(is_valid)

        # Invalid format
        invalid_datetime = "25/12/2023 3:30 PM"
        is_valid, error = self.validator.validate_datetime_string(
            invalid_datetime, "%Y-%m-%d %H:%M:%S", "timestamp"
        )
        self.assertFalse(is_valid)
        self.assertIn("invalid format", error)

    def test_validator_validation_report(self):
        """Test validation report creation."""
        validation_results = [
            ("item1", True, ""),
            ("item2", False, "Error message 1"),
            ("item3", True, ""),
            ("item4", False, "Error message 2"),
        ]

        report = self.validator.create_validation_report(validation_results)

        self.assertEqual(report["total_items"], 4)
        self.assertEqual(report["valid_items"], 2)
        self.assertEqual(report["invalid_items"], 2)
        self.assertEqual(report["success_rate"], 50.0)
        self.assertFalse(report["is_valid"])
        self.assertEqual(len(report["errors"]), 2)
        self.assertIn("timestamp", report)


if __name__ == "__main__":
    unittest.main()
