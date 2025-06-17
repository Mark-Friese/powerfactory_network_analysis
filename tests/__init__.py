"""
Test package for PowerFactory network analysis.

This package contains unit tests for all components of the
PowerFactory network analysis application.

Test Modules:
    test_models: Tests for data models (NetworkElement, AnalysisResult, Violation)
    test_analyzers: Tests for analysis components (ThermalAnalyzer, VoltageAnalyzer)
    test_core: Tests for core components (PowerFactoryInterface, ResultsManager)
    test_utils: Tests for utility components (FileHandler, InputValidator)
    
Usage:
    # Run all tests
    python test_runner.py
    
    # Run specific test module
    python -m unittest test_models
    
    # Run specific test class
    python -m unittest test_models.TestModels
    
    # Run specific test method
    python -m unittest test_models.TestModels.test_network_element_creation
"""

__version__ = "1.0.0"
__author__ = "PowerFactory Analysis Team"
