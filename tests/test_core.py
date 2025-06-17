"""
Tests for core components.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import sys
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from src.core.powerfactory_interface import PowerFactoryInterface
from src.core.results_manager import ResultsManager
from src.models.network_element import NetworkElement, ElementType, Region
from src.models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
from src.models.violation import Violation
from datetime import datetime


class TestCore(unittest.TestCase):
    """Test cases for core components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for testing
        PowerFactoryInterface._instance = None
        PowerFactoryInterface._app = None
        
        # Create test analysis results
        self.test_element = NetworkElement(
            name="Test_Element",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            powerfactory_object=Mock()
        )
        
        self.test_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION,
            contingency="Base Case",
            metadata={'test': 'data'}
        )
        
        self.test_violation = Violation(
            element_name="Test_Element",
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
    
    @patch('src.core.powerfactory_interface.POWERFACTORY_AVAILABLE', True)
    @patch('src.core.powerfactory_interface.pf')
    def test_powerfactory_interface_singleton(self, mock_pf):
        """Test PowerFactory interface singleton pattern."""
        # Create two instances
        interface1 = PowerFactoryInterface()
        interface2 = PowerFactoryInterface()
        
        # Should be the same object
        self.assertIs(interface1, interface2)
    
    @patch('src.core.powerfactory_interface.POWERFACTORY_AVAILABLE', True)
    @patch('src.core.powerfactory_interface.pf')
    def test_powerfactory_interface_connection(self, mock_pf):
        """Test PowerFactory interface connection."""
        # Mock PowerFactory application
        mock_app = Mock()
        mock_pf.GetApplication.return_value = mock_app
        
        interface = PowerFactoryInterface()
        
        # Test connection
        result = interface.connect()
        self.assertTrue(result)
        self.assertTrue(interface.is_connected)
        self.assertEqual(interface.app, mock_app)
        
        # Test disconnection
        interface.disconnect()
        self.assertFalse(interface.is_connected)
        self.assertIsNone(interface.app)
    
    @patch('src.core.powerfactory_interface.POWERFACTORY_AVAILABLE', True)
    @patch('src.core.powerfactory_interface.pf')
    def test_powerfactory_interface_operations(self, mock_pf):
        """Test PowerFactory interface operations."""
        # Mock PowerFactory application
        mock_app = Mock()
        mock_pf.GetApplication.return_value = mock_app
        
        # Mock study case
        mock_study_case = Mock()
        mock_app.GetActiveStudyCase.return_value = mock_study_case
        
        # Mock objects
        mock_objects = [Mock(), Mock()]
        mock_app.GetCalcRelevantObjects.return_value = mock_objects
        
        # Mock load flow command
        mock_ldf = Mock()
        mock_ldf.Execute.return_value = 0  # Success
        mock_app.GetFromStudyCase.return_value = mock_ldf
        
        interface = PowerFactoryInterface()
        interface.connect()
        
        # Test get active study case
        study_case = interface.get_active_study_case()
        self.assertEqual(study_case, mock_study_case)
        
        # Test get calc relevant objects
        objects = interface.get_calc_relevant_objects('*.ElmLne')
        self.assertEqual(objects, mock_objects)
        mock_app.GetCalcRelevantObjects.assert_called_with('*.ElmLne')
        
        # Test execute load flow
        result = interface.execute_load_flow()
        self.assertTrue(result)
        mock_ldf.Execute.assert_called_once()
    
    @patch('src.core.powerfactory_interface.POWERFACTORY_AVAILABLE', False)
    def test_powerfactory_interface_unavailable(self):
        """Test PowerFactory interface when PowerFactory is unavailable."""
        with self.assertRaises(ImportError):
            PowerFactoryInterface()
    
    def test_results_manager_initialization(self):
        """Test ResultsManager initialization."""
        results_manager = ResultsManager()
        
        self.assertIsInstance(results_manager.base_case_results, dict)
        self.assertIsInstance(results_manager.contingency_results, dict)
        self.assertEqual(len(results_manager.base_case_results), 0)
        self.assertEqual(len(results_manager.contingency_results), 0)
    
    def test_results_manager_add_results(self):
        """Test adding results to ResultsManager."""
        results_manager = ResultsManager()
        
        # Add base case results
        thermal_results = [self.test_result]
        results_manager.add_base_case_results('thermal', thermal_results)
        
        self.assertIn('thermal', results_manager.base_case_results)
        self.assertEqual(len(results_manager.base_case_results['thermal']), 1)
        self.assertEqual(results_manager.base_case_results['thermal'][0], self.test_result)
        
        # Add contingency results
        voltage_results = [self.test_result]
        results_manager.add_contingency_results('Contingency_1', 'voltage', voltage_results)
        
        self.assertIn('Contingency_1', results_manager.contingency_results)
        self.assertIn('voltage', results_manager.contingency_results['Contingency_1'])
        self.assertEqual(len(results_manager.contingency_results['Contingency_1']['voltage']), 1)
    
    def test_results_manager_violations_extraction(self):
        """Test violation extraction from results."""
        results_manager = ResultsManager()
        
        # Create violation and normal results
        violation_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        
        normal_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=75.0,
            limit=90.0,
            status=ResultStatus.NORMAL
        )
        
        results = [violation_result, normal_result]
        results_manager.add_base_case_results('thermal', results)
        
        # Get all violations
        violations = results_manager.get_all_violations()
        
        self.assertEqual(len(violations), 1)  # Only one violation
        self.assertEqual(violations[0].element_name, "Test_Element")
        self.assertEqual(violations[0].violation_value, 95.0)
        self.assertEqual(violations[0].scenario, "Base Case")
    
    def test_results_manager_violation_filtering(self):
        """Test violation filtering methods."""
        results_manager = ResultsManager()
        
        # Create thermal violation
        thermal_violation_result = AnalysisResult(
            timestamp=datetime.now(),
            element=self.test_element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        
        # Create voltage violation
        voltage_element = NetworkElement(
            name="Test_Bus",
            element_type=ElementType.BUSBAR,
            voltage_level=33.0,
            region=Region.ENGLAND,
            powerfactory_object=Mock()
        )
        
        voltage_violation_result = AnalysisResult(
            timestamp=datetime.now(),
            element=voltage_element,
            analysis_type=AnalysisType.VOLTAGE,
            value=0.93,
            limit=0.95,
            status=ResultStatus.VIOLATION
        )
        
        results_manager.add_base_case_results('thermal', [thermal_violation_result])
        results_manager.add_base_case_results('voltage', [voltage_violation_result])
        
        # Test filtering by analysis type
        thermal_violations = results_manager.get_violations_by_type(AnalysisType.THERMAL)
        self.assertEqual(len(thermal_violations), 1)
        self.assertEqual(thermal_violations[0].analysis_type, AnalysisType.THERMAL)
        
        voltage_violations = results_manager.get_violations_by_type(AnalysisType.VOLTAGE)
        self.assertEqual(len(voltage_violations), 1)
        self.assertEqual(voltage_violations[0].analysis_type, AnalysisType.VOLTAGE)
        
        # Test filtering by region
        scotland_violations = results_manager.get_violations_by_region(Region.SCOTLAND)
        self.assertEqual(len(scotland_violations), 1)
        self.assertEqual(scotland_violations[0].region, Region.SCOTLAND)
        
        england_violations = results_manager.get_violations_by_region(Region.ENGLAND)
        self.assertEqual(len(england_violations), 1)
        self.assertEqual(england_violations[0].region, Region.ENGLAND)
        
        # Test filtering by voltage level
        violations_33kv = results_manager.get_violations_by_voltage_level(33.0)
        self.assertEqual(len(violations_33kv), 2)  # Both violations are 33kV
    
    def test_results_manager_summary_statistics(self):
        """Test summary statistics generation."""
        results_manager = ResultsManager()
        
        # Add test results with violations
        violation_results = []
        for i in range(3):
            violation_result = AnalysisResult(
                timestamp=datetime.now(),
                element=self.test_element,
                analysis_type=AnalysisType.THERMAL,
                value=95.0 + i,
                limit=90.0,
                status=ResultStatus.VIOLATION
            )
            violation_results.append(violation_result)
        
        results_manager.add_base_case_results('thermal', violation_results)
        
        # Get summary statistics
        stats = results_manager.get_summary_statistics()
        
        self.assertEqual(stats['total_violations'], 3)
        self.assertEqual(stats['base_case_violations'], 3)
        self.assertEqual(stats['contingency_violations'], 0)
        self.assertEqual(stats['thermal_violations'], 3)
        self.assertEqual(stats['voltage_violations'], 0)
        
        # Check severity breakdown
        self.assertIn('severity_breakdown', stats)
        self.assertIn('regional_breakdown', stats)
        self.assertIn('contingency_statistics', stats)
    
    def test_results_manager_worst_contingencies(self):
        """Test worst contingencies identification."""
        results_manager = ResultsManager()
        
        # Add contingency results with different violation counts
        for i, contingency_name in enumerate(['Cont_1', 'Cont_2', 'Cont_3']):
            violation_count = i + 1  # 1, 2, 3 violations respectively
            violations = []
            
            for j in range(violation_count):
                violation_result = AnalysisResult(
                    timestamp=datetime.now(),
                    element=self.test_element,
                    analysis_type=AnalysisType.THERMAL,
                    value=95.0,
                    limit=90.0,
                    status=ResultStatus.VIOLATION
                )
                violations.append(violation_result)
            
            results_manager.add_contingency_results(contingency_name, 'thermal', violations)
        
        # Get worst contingencies
        worst_contingencies = results_manager.get_worst_contingencies(top_n=2)
        
        self.assertEqual(len(worst_contingencies), 2)
        # Should be sorted by violation count (descending)
        self.assertEqual(worst_contingencies[0]['contingency_name'], 'Cont_3')
        self.assertEqual(worst_contingencies[0]['total_violations'], 3)
        self.assertEqual(worst_contingencies[1]['contingency_name'], 'Cont_2')
        self.assertEqual(worst_contingencies[1]['total_violations'], 2)
    
    def test_results_manager_export_to_dict(self):
        """Test results export to dictionary."""
        results_manager = ResultsManager()
        
        # Add some test data
        results_manager.add_base_case_results('thermal', [self.test_result])
        
        # Export to dictionary
        export_data = results_manager.export_results_to_dict()
        
        self.assertIn('timestamp', export_data)
        self.assertIn('summary_statistics', export_data)
        self.assertIn('violations', export_data)
        self.assertIn('base_case_results', export_data)
        self.assertIn('contingency_results', export_data)
        
        # Check violations data
        self.assertEqual(len(export_data['violations']), 1)
        self.assertEqual(export_data['violations'][0]['element_name'], 'Test_Element')
    
    def test_results_manager_asset_loading_summary(self):
        """Test asset loading summary."""
        results_manager = ResultsManager()
        
        # Create thermal results with different loading values
        thermal_results = []
        loading_values = [50, 75, 85, 95, 105]  # Mix of normal and overloaded
        
        for loading in loading_values:
            status = ResultStatus.VIOLATION if loading > 90 else ResultStatus.NORMAL
            result = AnalysisResult(
                timestamp=datetime.now(),
                element=self.test_element,
                analysis_type=AnalysisType.THERMAL,
                value=loading,
                limit=90.0,
                status=status
            )
            thermal_results.append(result)
        
        results_manager.add_base_case_results('thermal', thermal_results)
        
        # Get asset loading summary
        summary = results_manager.get_asset_loading_summary()
        
        self.assertEqual(summary['total_elements'], 5)
        self.assertEqual(summary['max_loading'], 105)
        self.assertEqual(summary['min_loading'], 50)
        self.assertEqual(summary['avg_loading'], 82.0)
        self.assertEqual(summary['elements_over_90'], 2)  # 95, 105
        self.assertEqual(summary['elements_over_100'], 1)  # 105
        
        # Check loading distribution
        self.assertIn('loading_distribution', summary)
        self.assertEqual(summary['loading_distribution']['0-50%'], 1)  # 50
        self.assertEqual(summary['loading_distribution']['50-75%'], 0)
        self.assertEqual(summary['loading_distribution']['75-90%'], 2)  # 75, 85
        self.assertEqual(summary['loading_distribution']['>100%'], 1)  # 105


if __name__ == "__main__":
    unittest.main()
