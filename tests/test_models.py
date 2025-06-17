"""
Tests for data models.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock

import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from src.models.network_element import NetworkElement, ElementType, Region
from src.models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
from src.models.violation import Violation


class TestModels(unittest.TestCase):
    """Test cases for data models."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PowerFactory object
        self.mock_pf_object = Mock()
        self.mock_pf_object.GetAttribute.return_value = 100.0
        
        # Create test network element
        self.test_element = NetworkElement(
            name="Test_Line_001",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            powerfactory_object=self.mock_pf_object
        )
    
    def test_network_element_creation(self):
        """Test NetworkElement creation."""
        self.assertEqual(self.test_element.name, "Test_Line_001")
        self.assertEqual(self.test_element.element_type, ElementType.LINE)
        self.assertEqual(self.test_element.voltage_level, 33.0)
        self.assertEqual(self.test_element.region, Region.SCOTLAND)
        self.assertTrue(self.test_element.operational_status)
        self.assertIsNotNone(self.test_element.properties)
    
    def test_thermal_element_properties(self):
        """Test thermal element identification."""
        # Line should be thermal element
        line = NetworkElement("line", ElementType.LINE, 33.0, Region.SCOTLAND, None)
        self.assertTrue(line.is_thermal_element)
        self.assertFalse(line.is_voltage_element)
        
        # Transformer should be thermal element
        transformer = NetworkElement("tx", ElementType.TRANSFORMER_2W, 33.0, Region.SCOTLAND, None)
        self.assertTrue(transformer.is_thermal_element)
        self.assertFalse(transformer.is_voltage_element)
        
        # Busbar should be voltage element
        busbar = NetworkElement("bus", ElementType.BUSBAR, 33.0, Region.SCOTLAND, None)
        self.assertFalse(busbar.is_thermal_element)
        self.assertTrue(busbar.is_voltage_element)
    
    def test_powerfactory_attribute_access(self):
        """Test PowerFactory attribute access."""
        attribute_value = self.test_element.get_powerfactory_attribute('test_attr')
        self.assertEqual(attribute_value, 100.0)
        self.mock_pf_object.GetAttribute.assert_called_with('test_attr')
    
    def test_out_of_service_control(self):
        """Test out of service functionality."""
        # Mock the outserv attribute
        self.mock_pf_object.outserv = 0
        
        # Set out of service
        result = self.test_element.set_out_of_service(True)
        self.assertTrue(result)
        self.assertEqual(self.mock_pf_object.outserv, 1)
        self.assertFalse(self.test_element.operational_status)
        
        # Set back in service
        result = self.test_element.set_out_of_service(False)
        self.assertTrue(result)
        self.assertEqual(self.mock_pf_object.outserv, 0)
        self.assertTrue(self.test_element.operational_status)
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation."""
        timestamp = datetime.now()
        
        result = AnalysisResult(
            timestamp=timestamp,
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        
        self.assertEqual(result.timestamp, timestamp)
        self.assertEqual(result.element, self.test_element)
        self.assertEqual(result.analysis_type, AnalysisType.THERMAL)
        self.assertEqual(result.value, 95.0)
        self.assertEqual(result.limit, 90.0)
        self.assertEqual(result.status, ResultStatus.VIOLATION)
        self.assertTrue(result.is_violation)
        self.assertFalse(result.is_warning)
    
    def test_analysis_result_properties(self):
        """Test AnalysisResult properties."""
        # Violation result
        violation_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        self.assertTrue(violation_result.is_violation)
        self.assertFalse(violation_result.is_warning)
        
        # Warning result
        warning_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=85.0,
            limit=90.0,
            status=ResultStatus.WARNING
        )
        self.assertFalse(warning_result.is_violation)
        self.assertTrue(warning_result.is_warning)
        
        # Normal result
        normal_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=75.0,
            limit=90.0,
            status=ResultStatus.NORMAL
        )
        self.assertFalse(normal_result.is_violation)
        self.assertFalse(normal_result.is_warning)
    
    def test_violation_creation(self):
        """Test Violation creation."""
        timestamp = datetime.now()
        
        violation = Violation(
            element_name="Test_Line_001",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            analysis_type=AnalysisType.THERMAL,
            violation_value=95.0,
            limit_value=90.0,
            severity="High",
            scenario="Base Case",
            timestamp=timestamp
        )
        
        self.assertEqual(violation.element_name, "Test_Line_001")
        self.assertEqual(violation.element_type, ElementType.LINE)
        self.assertEqual(violation.voltage_level, 33.0)
        self.assertEqual(violation.region, Region.SCOTLAND)
        self.assertEqual(violation.analysis_type, AnalysisType.THERMAL)
        self.assertEqual(violation.violation_value, 95.0)
        self.assertEqual(violation.limit_value, 90.0)
        self.assertEqual(violation.severity, "High")
        self.assertEqual(violation.scenario, "Base Case")
        self.assertEqual(violation.timestamp, timestamp)
    
    def test_violation_serialization(self):
        """Test Violation to_dict method."""
        violation = Violation(
            element_name="Test_Line_001",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            analysis_type=AnalysisType.THERMAL,
            violation_value=95.0,
            limit_value=90.0,
            severity="High",
            scenario="Base Case",
            timestamp=datetime.now()
        )
        
        violation_dict = violation.to_dict()
        
        self.assertIsInstance(violation_dict, dict)
        self.assertEqual(violation_dict['element_name'], "Test_Line_001")
        self.assertEqual(violation_dict['element_type'], ElementType.LINE.value)
        self.assertEqual(violation_dict['region'], Region.SCOTLAND.value)
        self.assertEqual(violation_dict['analysis_type'], AnalysisType.THERMAL.value)
    
    def test_enum_values(self):
        """Test enum values are correct."""
        # ElementType values
        self.assertEqual(ElementType.LINE.value, "ElmLne")
        self.assertEqual(ElementType.TRANSFORMER_2W.value, "ElmTr2")
        self.assertEqual(ElementType.BUSBAR.value, "ElmTerm")
        
        # Region values
        self.assertEqual(Region.SCOTLAND.value, "scotland")
        self.assertEqual(Region.ENGLAND.value, "england")
        
        # AnalysisType values
        self.assertEqual(AnalysisType.THERMAL.value, "thermal")
        self.assertEqual(AnalysisType.VOLTAGE.value, "voltage")
        
        # ResultStatus values
        self.assertEqual(ResultStatus.NORMAL.value, "normal")
        self.assertEqual(ResultStatus.WARNING.value, "warning")
        self.assertEqual(ResultStatus.VIOLATION.value, "violation")


if __name__ == "__main__":
    unittest.main()
