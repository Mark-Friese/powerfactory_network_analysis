#!/usr/bin/env python3
"""
Main execution script for PowerFactory network analysis.

This script provides a command-line interface for running PowerFactory
network analysis including thermal and voltage analysis with contingencies.

Usage:
    python run_analysis.py [options]

Examples:
    # Run with default configuration
    python run_analysis.py

    # Run with custom config
    python run_analysis.py --config custom_config.yaml

    # Run only base case analysis
    python run_analysis.py --base-case-only

    # Generate only CSV reports
    python run_analysis.py --format csv
"""

import argparse
import sys
import traceback
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to Python path for src imports
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.core.network_analyzer import NetworkAnalyzer
from src.core.results_manager import ResultsManager
from src.reports.excel_reporter import ExcelReporter
from src.reports.csv_reporter import CSVReporter
from src.utils.logger import AnalysisLogger, get_logger
from src.utils.file_handler import FileHandler
from src.utils.validation import InputValidator


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = get_logger("run_analysis")
    
    if log_file:
        # Additional file handler if specified
        import logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PowerFactory Network Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Run with default settings
  %(prog)s --config my_config.yaml      # Use custom configuration
  %(prog)s --base-case-only             # Skip contingency analysis
  %(prog)s --format csv                 # Generate only CSV reports
  %(prog)s --output-dir ./results       # Custom output directory
  %(prog)s --log-level DEBUG            # Enable debug logging
        """
    )
    
    # Configuration options
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to analysis configuration file (YAML)"
    )
    
    # Analysis options
    parser.add_argument(
        "--base-case-only", "-b",
        action="store_true",
        help="Run only base case analysis (skip contingencies)"
    )
    
    parser.add_argument(
        "--contingency-only",
        action="store_true",
        help="Run only contingency analysis (skip base case)"
    )
    
    parser.add_argument(
        "--max-contingencies", "-m",
        type=int,
        help="Maximum number of contingencies to analyze"
    )
    
    # Output options
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./output",
        help="Output directory for results and reports (default: ./output)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["excel", "csv", "both"],
        default="both",
        help="Output format for reports (default: both)"
    )
    
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="Skip report generation (analysis only)"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path (in addition to console logging)"
    )
    
    # Validation options
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup without running analysis"
    )
    
    # PowerFactory options
    parser.add_argument(
        "--user-id", "-u",
        type=str,
        help="PowerFactory user ID for authentication"
    )
    
    # Other options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output"
    )
    
    return parser.parse_args()


def validate_configuration(config_path: Optional[str], logger: AnalysisLogger) -> Optional[Dict[str, Any]]:
    """Validate and load configuration."""
    try:
        validator = InputValidator()
        file_handler = FileHandler()
        
        # Load configuration
        if config_path:
            # Validate config file path
            is_valid, error_msg = validator.validate_file_path(
                config_path, must_exist=True, allowed_extensions=['.yaml', '.yml']
            )
            if not is_valid:
                logger.error(f"Configuration file validation failed: {error_msg}")
                return None
            
            config = file_handler.read_yaml(config_path)
            if config is None:
                logger.error("Failed to load configuration file")
                return None
            
            logger.info(f"Loaded configuration from: {config_path}")
        else:
            # Use default configuration
            config_dir = Path(__file__).parent.parent / "config"
            analyzer = NetworkAnalyzer()
            config = analyzer.config
            logger.info("Using default configuration")
        
        # Validate configuration structure
        is_valid, errors = validator.validate_config_structure(config)
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return None
        
        logger.info("Configuration validation passed")
        return config
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return None


def setup_output_directory(output_dir: str, logger: AnalysisLogger) -> Optional[Path]:
    """Setup output directory structure."""
    try:
        validator = InputValidator()
        
        # Validate and create output directory
        is_valid, error_msg = validator.validate_directory_path(
            output_dir, must_exist=False, create_if_missing=True
        )
        if not is_valid:
            logger.error(f"Output directory validation failed: {error_msg}")
            return None
        
        output_path = Path(output_dir)
        
        # Create subdirectories
        subdirs = ["reports", "logs", "data"]
        for subdir in subdirs:
            (output_path / subdir).mkdir(exist_ok=True)
        
        logger.info(f"Output directory setup: {output_path.absolute()}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error setting up output directory: {e}")
        return None


def run_analysis(config: Dict[str, Any], args: argparse.Namespace, 
                output_path: Path, logger: AnalysisLogger) -> Optional[Dict[str, Any]]:
    """Run the network analysis."""
    try:
        logger.info("Starting PowerFactory network analysis")
        
        # Override configuration with command line arguments
        if args.base_case_only:
            config.setdefault('analysis', {}).setdefault('options', {})['run_contingency'] = False
        
        if args.contingency_only:
            config.setdefault('analysis', {}).setdefault('options', {})['run_base_case'] = False
        
        if args.max_contingencies:
            config.setdefault('analysis', {}).setdefault('options', {})['max_contingencies'] = args.max_contingencies
        
        # Initialize network analyzer
        analyzer = NetworkAnalyzer()
        analyzer.config = config
        
        # Get user ID from command line or config
        user_id = args.user_id or config.get('connection', {}).get('user_id')
        if user_id:
            analyzer.pf_interface.set_user_id(user_id)
            logger.info(f"PowerFactory user ID configured: {user_id}")
        
        # Validate analyzer setup
        if not analyzer._validate_analysis_configuration():
            logger.error("Analysis configuration validation failed")
            return None
        
        # Run analysis
        if args.dry_run:
            logger.info("Dry run completed successfully")
            return {"dry_run": True}
        
        # Connect to PowerFactory with user authentication
        if not analyzer.pf_interface.connect(user_id):
            logger.error("Failed to connect to PowerFactory")
            return None
        
        try:
            # Run full analysis
            results = analyzer.run_full_analysis()
            
            # Log summary
            summary = analyzer.get_analysis_summary()
            logger.info("Analysis completed successfully")
            logger.info(f"Analysis summary: {summary}")
            
            return results
            
        finally:
            # Always disconnect
            analyzer.disconnect()
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        if args.verbose:
            logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def generate_reports(results: Dict[str, Any], args: argparse.Namespace, 
                    output_path: Path, logger: AnalysisLogger) -> bool:
    """Generate analysis reports."""
    try:
        if args.no_reports:
            logger.info("Report generation skipped")
            return True
        
        logger.info("Generating analysis reports")
        
        # Initialize results manager
        results_manager = ResultsManager()
        results_manager.add_analysis_results(results)
        
        # Generate reports based on format
        reports_dir = output_path / "reports"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        success = True
        
        if args.format in ["excel", "both"]:
            try:
                excel_reporter = ExcelReporter()
                excel_path = reports_dir / f"network_analysis_{timestamp}.xlsx"
                
                if excel_reporter.generate_report(results_manager, excel_path):
                    logger.info(f"Excel report generated: {excel_path}")
                else:
                    logger.error("Excel report generation failed")
                    success = False
                    
            except ImportError:
                logger.warning("Excel reporting not available (missing dependencies)")
            except Exception as e:
                logger.error(f"Excel report generation failed: {e}")
                success = False
        
        if args.format in ["csv", "both"]:
            try:
                csv_reporter = CSVReporter()
                csv_dir = reports_dir / f"csv_{timestamp}"
                
                if csv_reporter.generate_reports(results_manager, csv_dir):
                    logger.info(f"CSV reports generated: {csv_dir}")
                else:
                    logger.error("CSV report generation failed")
                    success = False
                    
            except Exception as e:
                logger.error(f"CSV report generation failed: {e}")
                success = False
        
        # Save raw results to JSON
        try:
            file_handler = FileHandler()
            json_path = output_path / "data" / f"analysis_results_{timestamp}.json"
            
            if results_manager.save_results_to_json(json_path):
                logger.info(f"Raw results saved: {json_path}")
            
        except Exception as e:
            logger.warning(f"Failed to save raw results: {e}")
        
        return success
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return False


def main() -> int:
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Adjust log level for quiet/verbose modes
    log_level = args.log_level
    if args.quiet:
        log_level = "WARNING"
    elif args.verbose:
        log_level = "DEBUG"
    
    # Setup logging
    logger = setup_logging(log_level, args.log_file)
    
    try:
        logger.info("PowerFactory Network Analysis Tool")
        logger.info(f"Arguments: {vars(args)}")
        
        # Validate configuration
        config = validate_configuration(args.config, logger)
        if config is None:
            return 1
        
        # Config validation only mode
        if args.validate_config:
            logger.info("Configuration validation passed")
            return 0
        
        # Setup output directory
        output_path = setup_output_directory(args.output_dir, logger)
        if output_path is None:
            return 1
        
        # Run analysis
        results = run_analysis(config, args, output_path, logger)
        if results is None:
            return 1
        
        # Handle dry run
        if results.get("dry_run"):
            return 0
        
        # Generate reports
        if not generate_reports(results, args, output_path, logger):
            logger.warning("Some reports failed to generate")
        
        logger.info("Analysis completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            logger.error(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
