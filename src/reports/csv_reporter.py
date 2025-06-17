"""
CSV report generator for PowerFactory analysis results.
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd

from ..core.results_manager import ResultsManager
from ..models.violation import Violation
from ..models.analysis_result import AnalysisType
from ..utils.logger import AnalysisLogger


class CSVReporter:
    """
    CSV report generator for PowerFactory network analysis results.
    
    Creates CSV files for different analysis aspects that can be easily
    imported into other tools for further analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CSV reporter.
        
        Args:
            config: Reporter configuration
        """
        self.logger = AnalysisLogger(self.__class__.__name__)
        self.config = config or {}
        
        # CSV settings
        self.delimiter = self.config.get('csv', {}).get('delimiter', ',')
        self.include_headers = self.config.get('csv', {}).get('include_headers', True)
        
        self.logger.info("CSV reporter initialized")
    
    def generate_reports(self, results_manager: ResultsManager, 
                        output_dir: Union[str, Path]) -> bool:
        """
        Generate all CSV reports.
        
        Args:
            results_manager: Results manager with analysis data
            output_dir: Directory for output CSV files
            
        Returns:
            True if successful
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Generating CSV reports in: {output_path}")
            
            # Generate individual reports
            success = True
            success &= self.generate_violations_csv(results_manager, output_path / "violations.csv")
            success &= self.generate_thermal_csv(results_manager, output_path / "thermal_analysis.csv")
            success &= self.generate_voltage_csv(results_manager, output_path / "voltage_analysis.csv")
            success &= self.generate_contingency_csv(results_manager, output_path / "contingency_summary.csv")
            success &= self.generate_summary_csv(results_manager, output_path / "analysis_summary.csv")
            
            if success:
                self.logger.info("All CSV reports generated successfully")
            else:
                self.logger.warning("Some CSV reports failed to generate")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV reports: {e}")
            return False
    
    def generate_violations_csv(self, results_manager: ResultsManager, 
                               output_path: Union[str, Path]) -> bool:
        """Generate violations CSV report."""
        try:
            violations = results_manager.get_all_violations()
            
            if not violations:
                self.logger.info("No violations found, skipping violations CSV")
                return True
            
            # Create DataFrame
            violation_data = []
            for violation in violations:
                violation_data.append({
                    'element_name': violation.element_name,
                    'element_type': violation.element_type.value,
                    'voltage_level_kv': violation.voltage_level,
                    'region': violation.region.value,
                    'analysis_type': violation.analysis_type.value,
                    'violation_value': violation.violation_value,
                    'limit_value': violation.limit_value,
                    'deviation': abs(violation.violation_value - violation.limit_value),
                    'severity': violation.severity,
                    'scenario': violation.scenario,
                    'violation_type': violation.metadata.get('violation_type', ''),
                    'timestamp': violation.timestamp.isoformat() if violation.timestamp else ''
                })
            
            df = pd.DataFrame(violation_data)
            
            # Sort by severity and deviation
            severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
            df['severity_order'] = df['severity'].map(severity_order)
            df = df.sort_values(['severity_order', 'deviation'], ascending=[False, False])
            df = df.drop('severity_order', axis=1)
            
            # Save to CSV
            df.to_csv(output_path, 
                     sep=self.delimiter, 
                     index=False, 
                     header=self.include_headers)
            
            self.logger.info(f"Violations CSV generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate violations CSV: {e}")
            return False
    
    def generate_thermal_csv(self, results_manager: ResultsManager, 
                            output_path: Union[str, Path]) -> bool:
        """Generate thermal analysis CSV report."""
        try:
            thermal_violations = results_manager.get_violations_by_type(AnalysisType.THERMAL)
            
            if not thermal_violations:
                self.logger.info("No thermal violations found, skipping thermal CSV")
                return True
            
            # Create DataFrame
            thermal_data = []
            for violation in thermal_violations:
                thermal_data.append({
                    'element_name': violation.element_name,
                    'element_type': violation.element_type.value,
                    'voltage_level_kv': violation.voltage_level,
                    'region': violation.region.value,
                    'loading_percent': violation.violation_value,
                    'limit_percent': violation.limit_value,
                    'overload_percent': violation.violation_value - violation.limit_value,
                    'severity': violation.severity,
                    'scenario': violation.scenario,
                    'current_amps': violation.metadata.get('current_amps', ''),
                    'power_mw': violation.metadata.get('power_mw', ''),
                    'timestamp': violation.timestamp.isoformat() if violation.timestamp else ''
                })
            
            df = pd.DataFrame(thermal_data)
            
            # Sort by overload percentage
            df = df.sort_values('overload_percent', ascending=False)
            
            # Save to CSV
            df.to_csv(output_path, 
                     sep=self.delimiter, 
                     index=False, 
                     header=self.include_headers)
            
            self.logger.info(f"Thermal analysis CSV generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate thermal CSV: {e}")
            return False
    
    def generate_voltage_csv(self, results_manager: ResultsManager, 
                            output_path: Union[str, Path]) -> bool:
        """Generate voltage analysis CSV report."""
        try:
            voltage_violations = results_manager.get_violations_by_type(AnalysisType.VOLTAGE)
            
            if not voltage_violations:
                self.logger.info("No voltage violations found, skipping voltage CSV")
                return True
            
            # Create DataFrame
            voltage_data = []
            for violation in voltage_violations:
                voltage_data.append({
                    'bus_name': violation.element_name,
                    'voltage_level_kv': violation.voltage_level,
                    'region': violation.region.value,
                    'voltage_pu': violation.violation_value,
                    'limit_pu': violation.limit_value,
                    'deviation_pu': abs(violation.violation_value - violation.limit_value),
                    'violation_type': violation.metadata.get('violation_type', ''),
                    'severity': violation.severity,
                    'scenario': violation.scenario,
                    'voltage_kv': violation.metadata.get('voltage_kv', ''),
                    'angle_deg': violation.metadata.get('angle_deg', ''),
                    'min_limit_pu': violation.metadata.get('min_limit', ''),
                    'max_limit_pu': violation.metadata.get('max_limit', ''),
                    'timestamp': violation.timestamp.isoformat() if violation.timestamp else ''
                })
            
            df = pd.DataFrame(voltage_data)
            
            # Sort by deviation
            df = df.sort_values('deviation_pu', ascending=False)
            
            # Save to CSV
            df.to_csv(output_path, 
                     sep=self.delimiter, 
                     index=False, 
                     header=self.include_headers)
            
            self.logger.info(f"Voltage analysis CSV generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate voltage CSV: {e}")
            return False
    
    def generate_contingency_csv(self, results_manager: ResultsManager, 
                                output_path: Union[str, Path]) -> bool:
        """Generate contingency summary CSV report."""
        try:
            worst_contingencies = results_manager.get_worst_contingencies(100)  # Top 100
            
            if not worst_contingencies:
                self.logger.info("No contingency violations found, skipping contingency CSV")
                return True
            
            # Create DataFrame
            df = pd.DataFrame(worst_contingencies)
            
            # Save to CSV
            df.to_csv(output_path, 
                     sep=self.delimiter, 
                     index=False, 
                     header=self.include_headers)
            
            self.logger.info(f"Contingency summary CSV generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate contingency CSV: {e}")
            return False
    
    def generate_summary_csv(self, results_manager: ResultsManager, 
                            output_path: Union[str, Path]) -> bool:
        """Generate analysis summary CSV report."""
        try:
            stats = results_manager.get_summary_statistics()
            asset_summary = results_manager.get_asset_loading_summary()
            voltage_summary = results_manager.get_voltage_profile_summary()
            
            # Create summary data
            summary_data = []
            
            # Basic statistics
            summary_data.extend([
                {'category': 'Basic Statistics', 'metric': 'Total Violations', 'value': stats.get('total_violations', 0)},
                {'category': 'Basic Statistics', 'metric': 'Base Case Violations', 'value': stats.get('base_case_violations', 0)},
                {'category': 'Basic Statistics', 'metric': 'Contingency Violations', 'value': stats.get('contingency_violations', 0)},
                {'category': 'Basic Statistics', 'metric': 'Thermal Violations', 'value': stats.get('thermal_violations', 0)},
                {'category': 'Basic Statistics', 'metric': 'Voltage Violations', 'value': stats.get('voltage_violations', 0)}
            ])
            
            # Severity breakdown
            severity = stats.get('severity_breakdown', {})
            for level, count in severity.items():
                summary_data.append({
                    'category': 'Severity Breakdown',
                    'metric': f'{level.capitalize()} Violations',
                    'value': count
                })
            
            # Regional breakdown
            regional = stats.get('regional_breakdown', {})
            for region, count in regional.items():
                summary_data.append({
                    'category': 'Regional Breakdown',
                    'metric': f'{region.capitalize()} Violations',
                    'value': count
                })
            
            # Asset loading summary
            if asset_summary:
                summary_data.extend([
                    {'category': 'Asset Loading', 'metric': 'Total Elements', 'value': asset_summary.get('total_elements', 0)},
                    {'category': 'Asset Loading', 'metric': 'Max Loading (%)', 'value': asset_summary.get('max_loading', 0)},
                    {'category': 'Asset Loading', 'metric': 'Average Loading (%)', 'value': asset_summary.get('avg_loading', 0)},
                    {'category': 'Asset Loading', 'metric': 'Elements >90%', 'value': asset_summary.get('elements_over_90', 0)},
                    {'category': 'Asset Loading', 'metric': 'Elements >100%', 'value': asset_summary.get('elements_over_100', 0)}
                ])
            
            # Voltage summary
            if voltage_summary:
                summary_data.extend([
                    {'category': 'Voltage Profile', 'metric': 'Total Buses', 'value': voltage_summary.get('total_buses', 0)},
                    {'category': 'Voltage Profile', 'metric': 'Max Voltage (pu)', 'value': voltage_summary.get('max_voltage', 0)},
                    {'category': 'Voltage Profile', 'metric': 'Min Voltage (pu)', 'value': voltage_summary.get('min_voltage', 0)},
                    {'category': 'Voltage Profile', 'metric': 'Average Voltage (pu)', 'value': voltage_summary.get('avg_voltage', 0)},
                    {'category': 'Voltage Profile', 'metric': 'Buses <0.95 pu', 'value': voltage_summary.get('buses_under_95', 0)},
                    {'category': 'Voltage Profile', 'metric': 'Buses >1.05 pu', 'value': voltage_summary.get('buses_over_105', 0)}
                ])
            
            # Contingency statistics
            cont_stats = stats.get('contingency_statistics', {})
            summary_data.extend([
                {'category': 'Contingency Analysis', 'metric': 'Total Contingencies', 'value': cont_stats.get('total_contingencies_analyzed', 0)},
                {'category': 'Contingency Analysis', 'metric': 'Contingencies with Violations', 'value': cont_stats.get('contingencies_with_violations', 0)},
                {'category': 'Contingency Analysis', 'metric': 'Violation Rate (%)', 'value': cont_stats.get('contingency_violation_rate', 0)}
            ])
            
            # Add timestamp
            summary_data.append({
                'category': 'Report Info',
                'metric': 'Generated',
                'value': datetime.now().isoformat()
            })
            
            df = pd.DataFrame(summary_data)
            
            # Save to CSV
            df.to_csv(output_path, 
                     sep=self.delimiter, 
                     index=False, 
                     header=self.include_headers)
            
            self.logger.info(f"Analysis summary CSV generated: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary CSV: {e}")
            return False
    
    def generate_all_results_csv(self, results_manager: ResultsManager, 
                                output_path: Union[str, Path]) -> bool:
        """
        Generate single comprehensive CSV with all results.
        
        Args:
            results_manager: Results manager with analysis data
            output_path: Path for output CSV file
            
        Returns:
            True if successful
        """
        try:
            all_results = []
            
            # Base case results
            for analysis_type, results in results_manager.base_case_results.items():
                for result in results:
                    all_results.append({
                        'scenario': 'Base Case',
                        'analysis_type': result.analysis_type.value,
                        'element_name': result.element.name,
                        'element_type': result.element.element_type.value,
                        'voltage_level_kv': result.element.voltage_level,
                        'region': result.element.region.value,
                        'value': result.value,
                        'limit': result.limit,
                        'status': result.status.value,
                        'is_violation': result.is_violation,
                        'timestamp': result.timestamp.isoformat() if result.timestamp else ''
                    })
            
            # Contingency results
            for contingency_name, contingency_data in results_manager.contingency_results.items():
                for analysis_type, results in contingency_data.items():
                    for result in results:
                        all_results.append({
                            'scenario': contingency_name,
                            'analysis_type': result.analysis_type.value,
                            'element_name': result.element.name,
                            'element_type': result.element.element_type.value,
                            'voltage_level_kv': result.element.voltage_level,
                            'region': result.element.region.value,
                            'value': result.value,
                            'limit': result.limit,
                            'status': result.status.value,
                            'is_violation': result.is_violation,
                            'timestamp': result.timestamp.isoformat() if result.timestamp else ''
                        })
            
            if not all_results:
                self.logger.info("No results found, skipping comprehensive CSV")
                return True
            
            df = pd.DataFrame(all_results)
            
            # Sort by scenario, then by violations
            df = df.sort_values(['scenario', 'is_violation', 'value'], ascending=[True, False, False])
            
            # Save to CSV
            df.to_csv(output_path, 
                     sep=self.delimiter, 
                     index=False, 
                     header=self.include_headers)
            
            self.logger.info(f"Comprehensive CSV generated: {output_path} ({len(all_results)} records)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive CSV: {e}")
            return False
