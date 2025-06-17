#!/usr/bin/env python3
"""
Glenrothes area contingency analysis with BESS scenarios.

This script runs comprehensive contingency analysis for the Glenrothes area,
testing different BESS export/import combinations against priority asset outages.
"""

import sys
import argparse
from pathlib import Path
import yaml
from datetime import datetime
from typing import Dict, List, Any

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.core.network_analyzer import NetworkAnalyzer
from src.core.scenario_manager import ScenarioManager
from src.core.contingency_manager import ContingencyManager
from src.utils.logger import AnalysisLogger, get_logger
from src.reports.excel_reporter import ExcelReporter


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Glenrothes BESS Contingency Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config/glenrothes_analysis.yaml",
        help="Path to Glenrothes analysis configuration file"
    )
    
    parser.add_argument(
        "--bess-a-name",
        type=str,
        default="Glenrothes_BESS_A",
        help="Name of first BESS unit in PowerFactory model"
    )
    
    parser.add_argument(
        "--bess-b-name", 
        type=str,
        default="Glenrothes_BESS_B",
        help="Name of second BESS unit in PowerFactory model"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./output/glenrothes",
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--max-contingencies",
        type=int,
        default=50,
        help="Maximum number of contingencies to analyze per scenario"
    )
    
    parser.add_argument(
        "--area-pattern",
        type=str,
        default="Glenrothes*",
        help="Pattern to filter network elements by area"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate setup without running analysis"
    )
    
    return parser.parse_args()


def setup_logging(log_level: str) -> AnalysisLogger:
    """Setup logging configuration."""
    return get_logger("glenrothes_analysis", log_level)


def load_configuration(config_path: str, logger: AnalysisLogger) -> Dict[str, Any]:
    """Load and validate configuration."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from: {config_path}")
        return config
        
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Creating default configuration template...")
        create_default_config(config_path)
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def create_default_config(config_path: str):
    """Create default configuration template."""
    config_dir = Path(config_path).parent
    config_dir.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        'analysis': {
            'thermal_limits': {
                'default': 90.0,
                'transformers': 85.0,
                'lines': 90.0,
                'reactors': 70.0
            },
            'voltage_limits': {
                'scotland': {
                    33.0: {'min': 0.97, 'max': 1.04},
                    11.0: {'min': 0.95, 'max': 1.05}
                }
            },
            'options': {
                'run_base_case': True,
                'run_contingency': True,
                'max_contingencies': 100,
                'include_out_of_service': False
            }
        },
        'regions': {
            'scotland': {
                'name': "Scotland",
                'voltage_levels': [33.0, 11.0]
            }
        },
        'contingencies': {
            'priority_assets': [
                {'pattern': "*33/11*Transformer*", 'type': "ElmTr2", 'description': "Primary transformers"},
                {'pattern': "*33kV*Feeder*", 'type': "ElmLne", 'description': "33kV primary feeders"},
                {'pattern': "*Bus*Section*", 'type': "ElmCoup", 'description': "Bus-section switches"},
                {'pattern': "*Reactor*", 'type': "ElmReac", 'description': "Bus-section reactors"}
            ]
        },
        'output': {
            'formats': ['excel', 'csv'],
            'include_scenarios': True,
            'scenario_comparison': True
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    print(f"Created default configuration: {config_path}")
    print("Please update BESS and asset names to match your PowerFactory model.")


def filter_elements_by_area(elements: List, area_pattern: str, logger: AnalysisLogger) -> List:
    """Filter network elements by geographic area."""
    import fnmatch
    
    filtered_elements = []
    for element in elements:
        # Check if element name matches area pattern
        if fnmatch.fnmatch(element.name, area_pattern):
            filtered_elements.append(element)
    
    logger.info(f"Filtered to {len(filtered_elements)} elements for area: {area_pattern}")
    return filtered_elements


def identify_contingency_assets(elements: List, config: Dict[str, Any], logger: AnalysisLogger) -> List:
    """Identify priority assets for contingency analysis."""
    import fnmatch
    
    contingency_assets = []
    priority_patterns = config.get('contingencies', {}).get('priority_assets', [])
    
    for element in elements:
        for pattern_config in priority_patterns:
            pattern = pattern_config.get('pattern', '')
            element_type = pattern_config.get('type', '')
            
            # Check if element matches pattern and type
            if (fnmatch.fnmatch(element.name, pattern) and
                element.element_type.value == element_type and
                element.voltage_level >= 11.0):  # Focus on 11kV and above
                contingency_assets.append(element)
                break
    
    logger.info(f"Identified {len(contingency_assets)} priority contingency assets")
    return contingency_assets


def run_scenario_analysis(analyzer: NetworkAnalyzer, scenario_manager: ScenarioManager,
                         scenarios: List, elements: List, contingency_assets: List,
                         max_contingencies: int, logger: AnalysisLogger) -> Dict[str, Any]:
    """Run analysis for all scenarios."""
    
    all_results = {}
    total_scenarios = len(scenarios)
    
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"Running scenario {i}/{total_scenarios}: {scenario.name}")
        
        # Apply scenario
        if not scenario_manager.apply_scenario(scenario):
            logger.warning(f"Failed to apply scenario: {scenario.name}")
            continue
        
        scenario_results = {
            'scenario': scenario,
            'base_case': {},
            'contingencies': {}
        }
        
        # Run base case for this scenario
        try:
            if analyzer.pf_interface.execute_load_flow():
                scenario_results['base_case'] = {
                    'thermal': analyzer.thermal_analyzer.analyze_network(elements),
                    'voltage': analyzer.voltage_analyzer.analyze_network(elements)
                }
                logger.debug(f"Base case completed for scenario: {scenario.name}")
            else:
                logger.warning(f"Base case load flow failed for scenario: {scenario.name}")
                scenario_manager.restore_original_values()
                continue
        except Exception as e:
            logger.error(f"Base case analysis failed for scenario {scenario.name}: {e}")
            scenario_manager.restore_original_values()
            continue
        
        # Run contingency analysis for priority assets
        contingency_results = {}
        assets_to_analyze = contingency_assets[:max_contingencies]
        
        for j, asset in enumerate(assets_to_analyze, 1):
            logger.debug(f"  Contingency {j}/{len(assets_to_analyze)}: {asset.name}")
            
            try:
                # Apply contingency
                if analyzer.contingency_manager.apply_contingency(asset):
                    # Run load flow
                    if analyzer.pf_interface.execute_load_flow():
                        # Analyze results
                        contingency_results[asset.name] = {
                            'thermal': analyzer.thermal_analyzer.analyze_network(elements, asset.name),
                            'voltage': analyzer.voltage_analyzer.analyze_network(elements, asset.name)
                        }
                    else:
                        logger.debug(f"Load flow failed for contingency: {asset.name}")
                    
                    # Restore contingency
                    analyzer.contingency_manager.restore_contingency(asset)
                else:
                    logger.debug(f"Failed to apply contingency: {asset.name}")
            
            except Exception as e:
                logger.debug(f"Error in contingency {asset.name}: {e}")
                # Ensure restoration
                analyzer.contingency_manager.restore_contingency(asset)
        
        scenario_results['contingencies'] = contingency_results
        all_results[scenario.name] = scenario_results
        
        # Restore scenario
        scenario_manager.restore_original_values()
        logger.info(f"Completed scenario: {scenario.name}")
    
    return all_results


def generate_summary_report(results: Dict[str, Any], output_path: Path, logger: AnalysisLogger):
    """Generate summary analysis report."""
    try:
        import pandas as pd
        
        # Prepare summary data
        summary_data = []
        
        for scenario_name, scenario_results in results.items():
            # Count base case violations
            base_thermal_violations = 0
            base_voltage_violations = 0
            
            if 'thermal' in scenario_results['base_case']:
                base_thermal_violations = len([r for r in scenario_results['base_case']['thermal'] if r.is_violation])
            
            if 'voltage' in scenario_results['base_case']:
                base_voltage_violations = len([r for r in scenario_results['base_case']['voltage'] if r.is_violation])
            
            # Find worst contingency
            worst_contingency = ""
            max_total_violations = 0
            critical_contingencies = 0
            
            for contingency_name, contingency_results in scenario_results['contingencies'].items():
                thermal_violations = 0
                voltage_violations = 0
                
                if 'thermal' in contingency_results:
                    thermal_violations = len([r for r in contingency_results['thermal'] if r.is_violation])
                
                if 'voltage' in contingency_results:
                    voltage_violations = len([r for r in contingency_results['voltage'] if r.is_violation])
                
                total_violations = thermal_violations + voltage_violations
                
                if total_violations > max_total_violations:
                    max_total_violations = total_violations
                    worst_contingency = contingency_name
                
                if total_violations > 5:  # Threshold for "critical"
                    critical_contingencies += 1
            
            summary_data.append({
                'Scenario': scenario_name,
                'Base_Thermal_Violations': base_thermal_violations,
                'Base_Voltage_Violations': base_voltage_violations,
                'Total_Base_Violations': base_thermal_violations + base_voltage_violations,
                'Worst_Contingency': worst_contingency,
                'Max_Contingency_Violations': max_total_violations,
                'Critical_Contingencies': critical_contingencies
            })
        
        # Create DataFrame and save
        df = pd.DataFrame(summary_data)
        summary_path = output_path / "analysis_summary.csv"
        df.to_csv(summary_path, index=False)
        
        logger.info(f"Summary report generated: {summary_path}")
        
        # Print key findings
        logger.info("=== KEY FINDINGS ===")
        worst_base_case = df.loc[df['Total_Base_Violations'].idxmax()]
        logger.info(f"Worst base case scenario: {worst_base_case['Scenario']} ({worst_base_case['Total_Base_Violations']} violations)")
        
        worst_contingency_scenario = df.loc[df['Max_Contingency_Violations'].idxmax()]
        logger.info(f"Worst contingency scenario: {worst_contingency_scenario['Scenario']} - {worst_contingency_scenario['Worst_Contingency']} ({worst_contingency_scenario['Max_Contingency_Violations']} violations)")
        
        most_critical = df.loc[df['Critical_Contingencies'].idxmax()]
        logger.info(f"Most critical contingencies: {most_critical['Scenario']} ({most_critical['Critical_Contingencies']} critical contingencies)")
        
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")


def main() -> int:
    """Main execution function."""
    args = parse_arguments()
    logger = setup_logging(args.log_level)
    
    try:
        logger.info("Starting Glenrothes BESS contingency analysis")
        logger.info(f"Arguments: {vars(args)}")
        
        # Load configuration
        config = load_configuration(args.config, logger)
        
        # Create output directory
        output_path = Path(args.output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_path / f"analysis_{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        if args.dry_run:
            logger.info("Dry run completed successfully")
            return 0
        
        # Initialize analyzer
        analyzer = NetworkAnalyzer()
        analyzer.config.update(config)
        
        # Connect to PowerFactory
        if not analyzer.connect_to_powerfactory():
            logger.error("Failed to connect to PowerFactory")
            return 1
        
        try:
            # Initialize scenario manager
            scenario_manager = ScenarioManager(analyzer.pf_interface)
            
            # Create BESS scenarios
            bess_scenarios = scenario_manager.create_bess_scenarios(args.bess_a_name, args.bess_b_name)
            logger.info(f"Created {len(bess_scenarios)} BESS scenarios")
            
            # Load and filter network elements
            all_elements = analyzer.load_network_elements()
            area_elements = filter_elements_by_area(all_elements, args.area_pattern, logger)
            
            if not area_elements:
                logger.error(f"No elements found for area pattern: {args.area_pattern}")
                return 1
            
            # Identify contingency assets
            contingency_assets = identify_contingency_assets(area_elements, config, logger)
            
            if not contingency_assets:
                logger.error("No contingency assets identified")
                return 1
            
            # Run scenario analysis
            results = run_scenario_analysis(
                analyzer, scenario_manager, bess_scenarios, area_elements,
                contingency_assets, args.max_contingencies, logger
            )
            
            # Generate reports
            generate_summary_report(results, output_path, logger)
            
            # Save detailed results
            results_path = output_path / "detailed_results.yaml"
            with open(results_path, 'w') as f:
                # Convert results to serializable format
                serializable_results = {}
                for scenario_name, scenario_data in results.items():
                    serializable_results[scenario_name] = {
                        'scenario_name': scenario_data['scenario'].name,
                        'scenario_description': scenario_data['scenario'].description,
                        'base_case_violation_count': {
                            'thermal': len([r for r in scenario_data['base_case'].get('thermal', []) if r.is_violation]),
                            'voltage': len([r for r in scenario_data['base_case'].get('voltage', []) if r.is_violation])
                        },
                        'contingency_count': len(scenario_data['contingencies'])
                    }
                yaml.dump(serializable_results, f, default_flow_style=False)
            
            logger.info(f"Analysis completed successfully. Results saved to: {output_path}")
            return 0
            
        finally:
            analyzer.disconnect()
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
