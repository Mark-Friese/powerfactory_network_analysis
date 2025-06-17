#!/usr/bin/env python3
"""
Test script to check all imports and identify issues.
"""

import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_imports():
    """Test all module imports."""
    print("Testing PowerFactory Network Analysis imports...")
    print("=" * 60)
    
    test_results = []
    
    # Test core modules
    try:
        from src.core.powerfactory_interface import PowerFactoryInterface
        test_results.append(("✓", "src.core.powerfactory_interface"))
    except Exception as e:
        test_results.append(("✗", f"src.core.powerfactory_interface: {e}"))
    
    try:
        from src.core.network_analyzer import NetworkAnalyzer
        test_results.append(("✓", "src.core.network_analyzer"))
    except Exception as e:
        test_results.append(("✗", f"src.core.network_analyzer: {e}"))
    
    try:
        from src.core.contingency_manager import ContingencyManager
        test_results.append(("✓", "src.core.contingency_manager"))
    except Exception as e:
        test_results.append(("✗", f"src.core.contingency_manager: {e}"))
    
    try:
        from src.core.results_manager import ResultsManager
        test_results.append(("✓", "src.core.results_manager"))
    except Exception as e:
        test_results.append(("✗", f"src.core.results_manager: {e}"))
    
    # Test model modules
    try:
        from src.models.network_element import NetworkElement, ElementType, Region
        test_results.append(("✓", "src.models.network_element"))
    except Exception as e:
        test_results.append(("✗", f"src.models.network_element: {e}"))
    
    try:
        from src.models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
        test_results.append(("✓", "src.models.analysis_result"))
    except Exception as e:
        test_results.append(("✗", f"src.models.analysis_result: {e}"))
    
    try:
        from src.models.violation import Violation
        test_results.append(("✓", "src.models.violation"))
    except Exception as e:
        test_results.append(("✗", f"src.models.violation: {e}"))
    
    # Test analyzer modules
    try:
        from src.analyzers.base_analyzer import BaseAnalyzer
        test_results.append(("✓", "src.analyzers.base_analyzer"))
    except Exception as e:
        test_results.append(("✗", f"src.analyzers.base_analyzer: {e}"))
    
    try:
        from src.analyzers.thermal_analyzer import ThermalAnalyzer
        test_results.append(("✓", "src.analyzers.thermal_analyzer"))
    except Exception as e:
        test_results.append(("✗", f"src.analyzers.thermal_analyzer: {e}"))
    
    try:
        from src.analyzers.voltage_analyzer import VoltageAnalyzer
        test_results.append(("✓", "src.analyzers.voltage_analyzer"))
    except Exception as e:
        test_results.append(("✗", f"src.analyzers.voltage_analyzer: {e}"))
    
    # Test utility modules
    try:
        from src.utils.logger import AnalysisLogger, get_logger
        test_results.append(("✓", "src.utils.logger"))
    except Exception as e:
        test_results.append(("✗", f"src.utils.logger: {e}"))
    
    try:
        from src.utils.validation import InputValidator
        test_results.append(("✓", "src.utils.validation"))
    except Exception as e:
        test_results.append(("✗", f"src.utils.validation: {e}"))
    
    try:
        from src.utils.file_handler import FileHandler
        test_results.append(("✓", "src.utils.file_handler"))
    except Exception as e:
        test_results.append(("✗", f"src.utils.file_handler: {e}"))
    
    # Test report modules
    try:
        from src.reports.excel_reporter import ExcelReporter
        test_results.append(("✓", "src.reports.excel_reporter"))
    except Exception as e:
        test_results.append(("✗", f"src.reports.excel_reporter: {e}"))
    
    try:
        from src.reports.csv_reporter import CSVReporter
        test_results.append(("✓", "src.reports.csv_reporter"))
    except Exception as e:
        test_results.append(("✗", f"src.reports.csv_reporter: {e}"))
    
    # Test main script
    try:
        from scripts.run_analysis import main
        test_results.append(("✓", "scripts.run_analysis"))
    except Exception as e:
        test_results.append(("✗", f"scripts.run_analysis: {e}"))
    
    # Print results
    print("\nImport Test Results:")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for status, module in test_results:
        print(f"{status} {module}")
        if status == "✓":
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total: {len(test_results)} modules tested")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All imports successful!")
    else:
        print(f"\n⚠️  {failed} import issues found")
    
    return failed == 0


def test_basic_functionality():
    """Test basic functionality without PowerFactory."""
    print("\n\nTesting basic functionality...")
    print("=" * 60)
    
    try:
        # Test configuration loading
        from src.core.network_analyzer import NetworkAnalyzer
        analyzer = NetworkAnalyzer()
        print("✓ NetworkAnalyzer instantiation")
        
        # Test results manager
        from src.core.results_manager import ResultsManager
        results_manager = ResultsManager()
        print("✓ ResultsManager instantiation")
        
        # Test file handler
        from src.utils.file_handler import FileHandler
        file_handler = FileHandler()
        print("✓ FileHandler instantiation")
        
        # Test validation
        from src.utils.validation import InputValidator
        validator = InputValidator()
        print("✓ InputValidator instantiation")
        
        # Test models
        from src.models.network_element import NetworkElement, ElementType, Region
        from datetime import datetime
        
        # Create a mock network element
        element = NetworkElement(
            name="Test Element",
            element_type=ElementType.LINE,
            voltage_level=33.0,
            region=Region.SCOTLAND,
            powerfactory_object=None,  # Mock object
            operational_status=True
        )
        print("✓ NetworkElement creation")
        
        # Test analysis result
        from src.models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
        
        result = AnalysisResult(
            timestamp=datetime.now(),
            element=element,
            analysis_type=AnalysisType.THERMAL,
            value=95.0,
            limit=90.0,
            status=ResultStatus.VIOLATION
        )
        print("✓ AnalysisResult creation")
        
        # Test violation
        from src.models.violation import Violation
        violation = Violation.from_analysis_result(result)
        if violation:
            print("✓ Violation creation from AnalysisResult")
        else:
            print("✗ Violation creation failed")
        
        print("\n🎉 All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Basic functionality test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def test_configuration():
    """Test configuration loading."""
    print("\n\nTesting configuration loading...")
    print("=" * 60)
    
    try:
        from src.utils.file_handler import FileHandler
        file_handler = FileHandler()
        
        # Test config files
        config_dir = Path("config")
        
        if (config_dir / "analysis_config.yaml").exists():
            config = file_handler.read_yaml(config_dir / "analysis_config.yaml")
            if config:
                print("✓ analysis_config.yaml loaded successfully")
                print(f"  - Found {len(config)} top-level sections")
            else:
                print("✗ Failed to load analysis_config.yaml")
        else:
            print("⚠️  analysis_config.yaml not found")
        
        if (config_dir / "network_config.yaml").exists():
            config = file_handler.read_yaml(config_dir / "network_config.yaml")
            if config:
                print("✓ network_config.yaml loaded successfully")
            else:
                print("✗ Failed to load network_config.yaml")
        else:
            print("⚠️  network_config.yaml not found")
        
        # Test NetworkAnalyzer config loading
        from src.core.network_analyzer import NetworkAnalyzer
        analyzer = NetworkAnalyzer()
        if analyzer.config:
            print("✓ NetworkAnalyzer configuration loaded")
            print(f"  - Config sections: {list(analyzer.config.keys())}")
        else:
            print("✗ NetworkAnalyzer configuration not loaded")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Configuration test failed: {e}")
        return False


def main():
    """Main test function."""
    print("PowerFactory Network Analysis - Import and Functionality Test")
    print("=" * 80)
    
    # Run tests
    import_success = test_imports()
    functionality_success = test_basic_functionality()
    config_success = test_configuration()
    
    # Summary
    print("\n\nTest Summary")
    print("=" * 60)
    print(f"Import Tests:        {'PASS' if import_success else 'FAIL'}")
    print(f"Functionality Tests: {'PASS' if functionality_success else 'FAIL'}")
    print(f"Configuration Tests: {'PASS' if config_success else 'FAIL'}")
    
    overall_success = import_success and functionality_success and config_success
    print(f"\nOverall Status:      {'PASS' if overall_success else 'FAIL'}")
    
    if overall_success:
        print("\n🎉 All tests passed! The codebase appears to be working correctly.")
        print("\nNext steps:")
        print("1. Ensure PowerFactory is installed and running")
        print("2. Run: python scripts/run_analysis.py --dry-run")
        print("3. Run actual analysis with: python scripts/run_analysis.py")
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
