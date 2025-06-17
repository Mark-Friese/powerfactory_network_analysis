"""
PowerFactory Network Analysis Package

A comprehensive tool for automated distribution network analysis
supporting multi-regional configurations and contingency analysis.
"""

__version__ = "1.0.0"
__author__ = "Network Analysis Team"

from .core.network_analyzer import NetworkAnalyzer
from .models.analysis_result import AnalysisResult
from .models.violation import Violation

__all__ = [
    "NetworkAnalyzer",
    "AnalysisResult", 
    "Violation"
]
