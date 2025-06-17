#!/usr/bin/env python3
"""
Simple test to verify the key fixes are working.
"""

import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_core_fixes():
    """Test the core type fixes without PowerFactory dependency."""
    print("Testing Core Type Fixes (No PowerFactory Required)")
    print("=" * 60)
    
    # Mock PowerFactory module
    from unittest.mock import Mock
    if 'powerfactory' not in sys.modules:
        sys.modules['powerfactory'] = Mock()
        sys.modules['powerfactory'].GetApplication = Mock(return_value=None)
        sys.modules['powerfactory'].GetApplicationExt = Mock(return_value=None)
    
    results = []
    
    # Test 1: Import all modules successfully
    try:
        from src.models.network_element import NetworkElement, ElementType, Region
        from src.models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
        from src.models.violation import Violation
        results.append(("✓", "All model imports successful"))
    except Exception as e:
        results.append(("✗", f"Model imports failed: {e}"))
        return results
    
    # Test 2: Create mock objects
    try:
        from datetime import datetime
        
        element = NetworkElement(
            name="Test Element",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            powerfactory_object=None,
            operational_status=True
        )
        
        result1 = AnalysisResult(
            timestamp=datetime.now(),
            element=element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        
        result2 = AnalysisResult(
            timestamp=datetime.now(),
            element=element,
            analysis_type=AnalysisType.THERMAL,
            value=85.0,
            limit=90.0,
            status=ResultStatus.NORMAL
        )
        
        results.append(("✓", "Mock objects created successfully"))
        
    except Exception as e:
        results.append(("✗", f"Mock object creation failed: {e}"))
        return results
    
    # Test 3: Thermal Analyzer return type fix
    try:
        class MockPFInterface:
            def is_connected(self):
                return True
            def get_element_attribute(self, element, attribute):
                return None
            def set_element_attribute(self, element, attribute, value):
                return True
        
        from src.analyzers.thermal_analyzer import ThermalAnalyzer
        
        config = {'analysis': {'thermal_limits': {'default': 90.0}}}
        analyzer = ThermalAnalyzer(MockPFInterface(), config)
        
        # Test the fixed method
        distribution = analyzer.get_loading_distribution([result1, result2])
        assert isinstance(distribution, dict)
        assert 'bins' in distribution
        assert 'counts' in distribution
        assert 'total_elements' in distribution
        assert distribution['total_elements'] == 2
        
        # Test edge case (same values)
        same_dist = analyzer.get_loading_distribution([result1])
        assert isinstance(same_dist, dict)
        assert 'total_elements' in same_dist
        
        results.append(("✓", "ThermalAnalyzer.get_loading_distribution fixed"))
        
    except Exception as e:
        results.append(("✗", f"ThermalAnalyzer test failed: {e}"))
    
    # Test 4: Voltage Analyzer return type fix
    try:
        from src.analyzers.voltage_analyzer import VoltageAnalyzer
        
        config = {'analysis': {'voltage_limits': {'scotland': {'33.0': {'min': 0.97, 'max': 1.04}}}}}
        v_analyzer = VoltageAnalyzer(MockPFInterface(), config)
        
        voltage_result = AnalysisResult(
            timestamp=datetime.now(),
            element=element,
            analysis_type=AnalysisType.VOLTAGE,
            value=0.96,
            limit=0.97,
            status=ResultStatus.VIOLATION
        )
        
        profile = v_analyzer.get_voltage_profile([voltage_result])
        assert isinstance(profile, dict)
        assert 'voltage_levels' in profile
        assert 'voltages' in profile
        assert 'bus_names' in profile
        assert 'regions' in profile
        
        results.append(("✓", "VoltageAnalyzer.get_voltage_profile fixed"))
        
    except Exception as e:
        results.append(("✗", f"VoltageAnalyzer test failed: {e}"))
    
    # Test 5: Violation model fix
    try:
        violation = Violation.from_analysis_result(result1)
        assert violation is not None
        assert hasattr(violation, 'element_name')
        assert hasattr(violation, 'element_type')
        assert hasattr(violation, 'analysis_type')
        
        violation_dict = violation.to_dict()
        assert isinstance(violation_dict, dict)
        assert 'element_name' in violation_dict
        
        results.append(("✓", "Violation model structure fixed"))
        
    except Exception as e:
        results.append(("✗", f"Violation model test failed: {e}"))
    
    # Test 6: Logger return type fix
    try:
        import logging
        from scripts.run_analysis import setup_logging
        
        logger = setup_logging("INFO")
        assert isinstance(logger, logging.Logger)
        
        results.append(("✓", "Logger return type fixed"))
        
    except Exception as e:
        results.append(("✗", f"Logger test failed: {e}"))
    
    return results

def main():
    """Main test function."""
    print("PowerFactory Network Analysis - Core Type Fixes Test")
    print("=" * 80)
    
    results = test_core_fixes()
    
    # Print results
    print("\nTest Results:")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for status, description in results:
        print(f"{status} {description}")
        if status == "✓":
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All core type fixes are working!")
        print("\nType errors should now be resolved in VS Code.")
        print("\nNext steps:")
        print("1. Reload VS Code window (Ctrl+Shift+P -> 'Developer: Reload Window')")
        print("2. Check Problems panel should show 0 errors")
        print("3. Run full analysis when PowerFactory is available")
    else:
        print(f"\n⚠️  {failed} tests failed. Check the errors above.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
