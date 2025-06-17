"""
Tests for analysis components.
"""

import unittest
from unittest.mock import Mock, MagicMock

import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from src.analyzers.thermal_analyzer import ThermalAnalyzer
from src.analyzers.voltage_analyzer import VoltageAnalyzer
from src.models.network_element import NetworkElement, ElementType, Region
from src.models.analysis_result import AnalysisType, ResultStatus


class TestAnalyzers(unittest.TestCase):
    """Test cases for analyzer components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PowerFactory interface
        self.mock_pf_interface = Mock()
        self.mock_pf_interface.is_connected = True
        self.mock_pf_interface.get_element_attribute = Mock()
        
        # Test configuration
        self.test_config = {
            'analysis': {
                'thermal_limits': {
                    'default': 90.0,
                    'lines': 90.0,
                    'transformers': 85.0,
                    'cables': 90.0
                },
                'voltage_limits': {
                    'scotland': {
                        '33.0': {'min': 0.97, 'max': 1.04},
                        '11.0': {'min': 0.95, 'max': 1.05}
                    },
                    'england': {
                        '132.0': {'min': 0.97, 'max': 1.04},
                        '33.0': {'min': 0.97, 'max': 1.04},
                        '11.0': {'min': 0.95, 'max': 1.05}
                    }
                }
            }
        }
        
        # Create test elements
        self.test_line = self._create_test_element("Test_Line", ElementType.LINE, 33.0, Region.SCOTLAND)
        self.test_transformer = self._create_test_element("Test_TX", ElementType.TRANSFORMER_2W, 33.0, Region.SCOTLAND)
        self.test_busbar = self._create_test_element("Test_Bus", ElementType.BUSBAR, 33.0, Region.SCOTLAND)
        
        # Initialize analyzers
        self.thermal_analyzer = ThermalAnalyzer(self.mock_pf_interface, self.test_config)
        self.voltage_analyzer = VoltageAnalyzer(self.mock_pf_interface, self.test_config)
    
    def _create_test_element(self, name: str, element_type: ElementType, voltage: float, region: Region):
        """Helper to create test network elements."""
        mock_pf_obj = Mock()
        return NetworkElement(
            name=name,
            element_type=element_type,
            voltage_level=voltage,
            region=region,
            powerfactory_object=mock_pf_obj,
            operational_status=True
        )
    
    def test_thermal_analyzer_initialization(self):
        """Test ThermalAnalyzer initialization."""
        self.assertEqual(self.thermal_analyzer.get_analysis_type(), AnalysisType.THERMAL)
        self.assertEqual(self.thermal_analyzer.default_limit, 90.0)
        self.assertEqual(self.thermal_analyzer.element_limits[ElementType.LINE], 90.0)
        self.assertEqual(self.thermal_analyzer.element_limits[ElementType.TRANSFORMER_2W], 85.0)
    
    def test_thermal_analyzer_applicable_elements(self):
        """Test thermal analyzer element filtering."""
        elements = [self.test_line, self.test_transformer, self.test_busbar]
        applicable = self.thermal_analyzer.get_applicable_elements(elements)
        
        # Should include thermal elements only
        self.assertIn(self.test_line, applicable)
        self.assertIn(self.test_transformer, applicable)
        self.assertNotIn(self.test_busbar, applicable)
    
    def test_thermal_analyzer_limits(self):
        """Test thermal limit retrieval."""
        # Line should use line limit
        line_limit = self.thermal_analyzer.get_thermal_limit(self.test_line)
        self.assertEqual(line_limit, 90.0)
        
        # Transformer should use transformer limit
        tx_limit = self.thermal_analyzer.get_thermal_limit(self.test_transformer)
        self.assertEqual(tx_limit, 85.0)
    
    def test_thermal_analysis_violation(self):
        """Test thermal analysis with violation."""
        # Mock loading above limit
        self.mock_pf_interface.get_element_attribute.return_value = 95.0  # 95% loading
        
        result = self.thermal_analyzer.analyze_element(self.test_line)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.analysis_type, AnalysisType.THERMAL)
        self.assertEqual(result.value, 95.0)
        self.assertEqual(result.limit, 90.0)
        self.assertEqual(result.status, ResultStatus.VIOLATION)
        self.assertTrue(result.is_violation)
    
    def test_thermal_analysis_normal(self):
        """Test thermal analysis with normal loading."""
        # Mock loading below limit
        self.mock_pf_interface.get_element_attribute.return_value = 75.0  # 75% loading
        
        result = self.thermal_analyzer.analyze_element(self.test_line)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.analysis_type, AnalysisType.THERMAL)
        self.assertEqual(result.value, 75.0)
        self.assertEqual(result.limit, 90.0)
        self.assertEqual(result.status, ResultStatus.NORMAL)
        self.assertFalse(result.is_violation)
    
    def test_thermal_analysis_no_data(self):
        """Test thermal analysis with no data."""
        # Mock no loading data
        self.mock_pf_interface.get_element_attribute.return_value = None
        
        result = self.thermal_analyzer.analyze_element(self.test_line)
        
        self.assertIsNone(result)
    
    def test_voltage_analyzer_initialization(self):
        """Test VoltageAnalyzer initialization."""
        self.assertEqual(self.voltage_analyzer.get_analysis_type(), AnalysisType.VOLTAGE)
        self.assertIsNotNone(self.voltage_analyzer.voltage_limits)
    
    def test_voltage_analyzer_applicable_elements(self):
        """Test voltage analyzer element filtering."""
        elements = [self.test_line, self.test_transformer, self.test_busbar]
        applicable = self.voltage_analyzer.get_applicable_elements(elements)
        
        # Should include voltage elements only
        self.assertNotIn(self.test_line, applicable)
        self.assertNotIn(self.test_transformer, applicable)
        self.assertIn(self.test_busbar, applicable)
    
    def test_voltage_limits_retrieval(self):
        """Test voltage limits retrieval."""
        # Scotland 33kV bus
        scotland_bus = self._create_test_element("Scotland_Bus", ElementType.BUSBAR, 33.0, Region.SCOTLAND)
        min_limit, max_limit = self.voltage_analyzer.get_voltage_limits(scotland_bus)
        self.assertEqual(min_limit, 0.97)
        self.assertEqual(max_limit, 1.04)
        
        # England 132kV bus
        england_bus = self._create_test_element("England_Bus", ElementType.BUSBAR, 132.0, Region.ENGLAND)
        min_limit, max_limit = self.voltage_analyzer.get_voltage_limits(england_bus)
        self.assertEqual(min_limit, 0.97)
        self.assertEqual(max_limit, 1.04)
    
    def test_voltage_analysis_undervoltage(self):
        """Test voltage analysis with undervoltage."""
        # Mock voltage below minimum
        self.mock_pf_interface.get_element_attribute.return_value = 0.95  # Below 0.97 limit
        
        result = self.voltage_analyzer.analyze_element(self.test_busbar)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.analysis_type, AnalysisType.VOLTAGE)
        self.assertEqual(result.value, 0.95)
        self.assertEqual(result.limit, 0.97)  # Should use min limit
        self.assertEqual(result.status, ResultStatus.VIOLATION)
        self.assertTrue(result.is_violation)
        self.assertEqual(result.metadata['violation_type'], 'undervoltage')
    
    def test_voltage_analysis_overvoltage(self):
        """Test voltage analysis with overvoltage."""
        # Mock voltage above maximum
        self.mock_pf_interface.get_element_attribute.return_value = 1.06  # Above 1.04 limit
        
        result = self.voltage_analyzer.analyze_element(self.test_busbar)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.analysis_type, AnalysisType.VOLTAGE)
        self.assertEqual(result.value, 1.06)
        self.assertEqual(result.limit, 1.04)  # Should use max limit
        self.assertEqual(result.status, ResultStatus.VIOLATION)
        self.assertTrue(result.is_violation)
        self.assertEqual(result.metadata['violation_type'], 'overvoltage')
    
    def test_voltage_analysis_normal(self):
        """Test voltage analysis with normal voltage."""
        # Mock voltage within limits
        self.mock_pf_interface.get_element_attribute.return_value = 1.00  # Within limits
        
        result = self.voltage_analyzer.analyze_element(self.test_busbar)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.analysis_type, AnalysisType.VOLTAGE)
        self.assertEqual(result.value, 1.00)
        self.assertEqual(result.status, ResultStatus.NORMAL)
        self.assertFalse(result.is_violation)
    
    def test_analyzer_network_analysis(self):
        """Test network-wide analysis."""
        elements = [self.test_line, self.test_transformer, self.test_busbar]
        
        # Mock thermal loading
        def mock_thermal_attribute(element, attribute):
            if attribute == 'm:loading':
                return 85.0  # Normal loading
            return None
        
        self.mock_pf_interface.get_element_attribute.side_effect = mock_thermal_attribute
        
        # Run thermal analysis
        thermal_results = self.thermal_analyzer.analyze_network(elements)
        
        # Should have results for thermal elements only
        self.assertEqual(len(thermal_results), 2)  # Line and transformer
        
        # All results should be thermal type
        for result in thermal_results:
            self.assertEqual(result.analysis_type, AnalysisType.THERMAL)
    
    def test_analyzer_configuration_validation(self):
        """Test analyzer configuration validation."""
        # Valid configuration should pass
        self.assertTrue(self.thermal_analyzer.validate_configuration())
        self.assertTrue(self.voltage_analyzer.validate_configuration())
        
        # Test with invalid configuration
        invalid_config = {'analysis': {'thermal_limits': {'lines': -10}}}  # Invalid negative limit
        invalid_analyzer = ThermalAnalyzer(self.mock_pf_interface, invalid_config)
        self.assertFalse(invalid_analyzer.validate_configuration())
    
    def test_analyzer_summary_statistics(self):
        """Test summary statistics generation."""
        # Create mock results
        mock_results = []
        for i in range(5):
            mock_result = Mock()
            mock_result.value = 80.0 + i * 5  # 80, 85, 90, 95, 100
            mock_result.is_violation = (80.0 + i * 5) > 90.0  # Violations at 95, 100
            mock_results.append(mock_result)
        
        stats = self.thermal_analyzer.get_summary_statistics(mock_results)
        
        self.assertEqual(stats['total_elements'], 5)
        self.assertEqual(stats['violations'], 2)
        self.assertEqual(stats['violation_rate'], 40.0)
        self.assertEqual(stats['max_value'], 100.0)
        self.assertEqual(stats['min_value'], 80.0)
        self.assertEqual(stats['avg_value'], 90.0)


if __name__ == "__main__":
    unittest.main()
