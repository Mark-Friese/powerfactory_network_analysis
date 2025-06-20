#!/usr/bin/env python3
"""
Wrapper script for running PowerFactory network analysis from project root.

This script ensures proper Python path configuration and runs the main analysis.
Run this from the project root directory to avoid import issues.

Usage:
    python run_analysis.py [options]
"""

import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

# Import and run the main script
if __name__ == "__main__":
    from scripts.run_analysis import main
    sys.exit(main()) 