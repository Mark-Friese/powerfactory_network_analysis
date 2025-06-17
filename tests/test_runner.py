"""
Basic tests for PowerFactory network analysis components.
"""

import unittest
import sys
from pathlib import Path

# Add src to Python path for testing
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# Import test modules
from test_models import TestModels
from test_analyzers import TestAnalyzers
from test_core import TestCore
from test_utils import TestUtils


def run_all_tests():
    """Run all test suites."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestModels,
        TestAnalyzers,
        TestCore,
        TestUtils
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
