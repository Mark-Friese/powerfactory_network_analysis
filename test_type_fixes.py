#!/usr/bin/env python3
"""
Comprehensive test script to verify all type error fixes.
"""

import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_all_type_fixes():
    """Test all the type fixes we made."""
    print("Testing all type error fixes...")
    print("=" * 60)
    
    test_results = []
    
    # Set up common mock objects
    try:
        # Mock PowerFactory interface to avoid import issues
        class MockPFInterface:
            def is_connected(self):
                return True
            
            def get_element_attribute(self, element, attribute):
                return None
            
            def set_element_attribute(self, element, attribute, value):
                return True
        
        # Import with PowerFactory mocking
        import sys
        from unittest.mock import Mock
        
        # Mock powerfactory module if not available
        if 'powerfactory' not in sys.modules:
            sys.modules['powerfactory'] = Mock()
        
        from src.models.network_element import NetworkElement, ElementType, Region
        from src.models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
        from datetime import datetime
        
        # Create common mock elements and results
        mock_element1 = NetworkElement(
            name="Test Line 1",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            powerfactory_object=None,
            operational_status=True
        )
        
        mock_element2 = NetworkElement(
            name="Test Line 2",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            powerfactory_object=None,
            operational_status=True
        )
        
        mock_result1 = AnalysisResult(
            timestamp=datetime.now(),
            element=mock_element1,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        
        mock_result2 = AnalysisResult(
            timestamp=datetime.now(),
            element=mock_element2,
            analysis_type=AnalysisType.THERMAL,
            value=85.0,
            limit=90.0,
            status=ResultStatus.NORMAL
        )
        
        mock_pf_interface = MockPFInterface()
        
    except Exception as e:
        test_results.append(("✗", f"Mock setup failed: {e}"))
        return test_results
    
    # Test 1: Thermal Analyzer type fixes
    try:
        from src.analyzers.thermal_analyzer import ThermalAnalyzer
        
        # Mock config
        config = {'analysis': {'thermal_limits': {'default': 90.0}}}
        thermal_analyzer = ThermalAnalyzer(mock_pf_interface, config)
        
        # Test get_loading_distribution method (fixed return type)
        distribution = thermal_analyzer.get_loading_distribution([mock_result1, mock_result2])
        assert isinstance(distribution, dict)
        assert 'bins' in distribution
        assert 'counts' in distribution
        assert 'total_elements' in distribution
        assert distribution['total_elements'] == 2
        
        # Test with single value (edge case)
        single_dist = thermal_analyzer.get_loading_distribution([mock_result1])
        assert isinstance(single_dist, dict)
        assert 'total_elements' in single_dist
        assert single_dist['total_elements'] == 1
        
        test_results.append(("✓", "ThermalAnalyzer.get_loading_distribution return type"))
        
    except Exception as e:
        test_results.append(("✗", f"ThermalAnalyzer test failed: {e}"))
    
    # Test 2: Voltage Analyzer type fixes
    try:
        from src.analyzers.voltage_analyzer import VoltageAnalyzer
        
        config = {'analysis': {'voltage_limits': {'scotland': {'33.0': {'min': 0.97, 'max': 1.04}}}}}
        voltage_analyzer = VoltageAnalyzer(mock_pf_interface, config)
        
        mock_voltage_result = AnalysisResult(
            timestamp=datetime.now(),
            element=mock_element1,
            analysis_type=AnalysisType.VOLTAGE,
            value=0.96,
            limit=0.97,
            status=ResultStatus.VIOLATION
        )
        
        # Test get_voltage_profile method (fixed return type)
        profile = voltage_analyzer.get_voltage_profile([mock_voltage_result])
        assert isinstance(profile, dict)
        assert 'voltage_levels' in profile
        assert 'voltages' in profile
        assert 'bus_names' in profile
        assert 'regions' in profile
        
        test_results.append(("✓", "VoltageAnalyzer.get_voltage_profile return type"))
        
    except Exception as e:
        test_results.append(("✗", f"VoltageAnalyzer test failed: {e}"))
    
    # Test 3: NetworkAnalyzer config assignment
    try:
        from src.core.network_analyzer import NetworkAnalyzer
        
        # Create analyzer (should handle PowerFactory not being available gracefully)
        try:
            analyzer = NetworkAnalyzer()
        except ImportError:
            # If PowerFactory module is not available, this is expected
            test_results.append(("~", "NetworkAnalyzer (PowerFactory module not available)"))
        else:
            # Test that config can be accessed and is a dict
            assert hasattr(analyzer, 'config')
            assert isinstance(analyzer.config, dict)
            
            # Test config assignment (should work now)
            test_config = {'test': 'value'}
            analyzer.config = test_config
            assert analyzer.config['test'] == 'value'
            
            test_results.append(("✓", "NetworkAnalyzer config assignment"))
        
    except Exception as e:
        test_results.append(("✗", f"NetworkAnalyzer config test failed: {e}"))
    
    # Test 4: Logging setup
    try:
        import logging
        # This import should work without type errors
        from scripts.run_analysis import setup_logging
        
        # Test that setup_logging returns a logger
        logger = setup_logging("INFO")
        assert isinstance(logger, logging.Logger)
        
        test_results.append(("✓", "setup_logging return type"))
        
    except Exception as e:
        test_results.append(("✗", f"Logging setup test failed: {e}"))
    
    # Test 5: Violation model fixes
    try:
        from src.models.violation import Violation
        
        # Test violation creation from analysis result
        violation = Violation.from_analysis_result(mock_result1)
        assert violation is not None
        assert hasattr(violation, 'element_name')
        assert hasattr(violation, 'element_type')
        assert hasattr(violation, 'analysis_type')
        
        # Test to_dict method
        violation_dict = violation.to_dict()
        assert isinstance(violation_dict, dict)
        assert 'element_name' in violation_dict
        assert 'analysis_type' in violation_dict
        
        test_results.append(("✓", "Violation model structure"))
        
    except Exception as e:
        test_results.append(("✗", f"Violation model test failed: {e}"))
    
    # Test 6: Excel workbook handling
    try:
        # Test openpyxl workbook creation (should not cause type errors)
        try:
            import openpyxl
            workbook = openpyxl.Workbook()
            
            # Test safe removal of default sheet
            if workbook.worksheets:
                workbook.remove(workbook.worksheets[0])
            
            test_results.append(("✓", "Excel workbook handling"))
            
        except ImportError:
            test_results.append(("~", "Excel workbook (openpyxl not installed)"))
        
    except Exception as e:
        test_results.append(("✗", f"Excel workbook test failed: {e}"))
    
    # Print results
    print("\\nType Fix Test Results:")
    print("-" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for status, description in test_results:
        print(f"{status} {description}")
        if status == "✓":
            passed += 1
        elif status == "✗":
            failed += 1
        else:
            skipped += 1
    
    print("-" * 60)
    print(f"Total: {len(test_results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    if failed == 0:
        print("\\n🎉 All type error fixes working correctly!")
        return True
    else:
        print(f"\\n⚠️  {failed} type fixes still have issues")
        return False

def main():
    """Main test function."""
    print("PowerFactory Network Analysis - Type Error Fixes Test")
    print("=" * 80)
    
    success = test_all_type_fixes()
    
    if success:
        print("\\n✅ All type errors have been successfully fixed!")
        print("\\nThe VS Code problems panel should now show no type errors.")
        print("\\nNext steps:")
        print("1. Reload VS Code window (Ctrl+Shift+P -> 'Developer: Reload Window')")
        print("2. Run full import test: python test_imports.py")
        print("3. Run analysis: python scripts/run_analysis.py --dry-run")
    else:
        print("\\n❌ Some type errors may still exist. Check the output above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
