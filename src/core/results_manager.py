"""
Results manager for aggregating and processing analysis results.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import json

from ..models.analysis_result import AnalysisResult, AnalysisType, ResultStatus
from ..models.network_element import NetworkElement, Region, ElementType
from ..models.violation import Violation
from ..utils.logger import AnalysisLogger


class ResultsManager:
    """
    Centralized manager for analysis results processing and aggregation.
    
    Handles result collection, filtering, aggregation, and preparation
    for reporting across different analysis types and scenarios.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize results manager.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = AnalysisLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Results storage
        self.base_case_results: Dict[str, List[AnalysisResult]] = {}
        self.contingency_results: Dict[str, Dict[str, List[AnalysisResult]]] = {}
        
        # Processed results cache
        self._processed_violations: Optional[List[Violation]] = None
        self._summary_statistics: Optional[Dict[str, Any]] = None
        
        self.logger.info("Results manager initialized")
    
    def add_base_case_results(self, analysis_type: str, results: List[AnalysisResult]) -> None:
        """
        Add base case analysis results.
        
        Args:
            analysis_type: Type of analysis ('thermal', 'voltage')
            results: List of analysis results
        """
        self.base_case_results[analysis_type] = results
        self._clear_cache()
        self.logger.debug(f"Added {len(results)} base case {analysis_type} results")
    
    def add_contingency_results(self, contingency_name: str, analysis_type: str, 
                               results: List[AnalysisResult]) -> None:
        """
        Add contingency analysis results.
        
        Args:
            contingency_name: Name of contingency scenario
            analysis_type: Type of analysis ('thermal', 'voltage')
            results: List of analysis results
        """
        if contingency_name not in self.contingency_results:
            self.contingency_results[contingency_name] = {}
        
        self.contingency_results[contingency_name][analysis_type] = results
        self._clear_cache()
        self.logger.debug(f"Added {len(results)} {analysis_type} results for contingency {contingency_name}")
    
    def add_analysis_results(self, analysis_results: Dict[str, Any]) -> None:
        """
        Add complete analysis results from NetworkAnalyzer.
        
        Args:
            analysis_results: Complete analysis results dictionary
        """
        # Add base case results
        base_case = analysis_results.get('base_case', {})
        for analysis_type, results in base_case.items():
            self.add_base_case_results(analysis_type, results)
        
        # Add contingency results
        contingencies = analysis_results.get('contingencies', {})
        for contingency_name, contingency_data in contingencies.items():
            for analysis_type, results in contingency_data.items():
                self.add_contingency_results(contingency_name, analysis_type, results)
        
        self.logger.info("Added complete analysis results to manager")
    
    def get_all_violations(self, include_contingencies: bool = True) -> List[Violation]:
        """
        Get all violations across all analysis types and scenarios.
        
        Args:
            include_contingencies: Whether to include contingency violations
            
        Returns:
            List of violations
        """
        if self._processed_violations is not None:
            return self._processed_violations
        
        violations = []
        
        # Base case violations
        for analysis_type, results in self.base_case_results.items():
            base_violations = self._extract_violations(results, "Base Case", analysis_type)
            violations.extend(base_violations)
        
        # Contingency violations
        if include_contingencies:
            for contingency_name, contingency_data in self.contingency_results.items():
                for analysis_type, results in contingency_data.items():
                    cont_violations = self._extract_violations(results, contingency_name, analysis_type)
                    violations.extend(cont_violations)
        
        self._processed_violations = violations
        return violations
    
    def _extract_violations(self, results: List[AnalysisResult], scenario: str, 
                           analysis_type: str) -> List[Violation]:
        """Extract violations from analysis results."""
        violations = []
        
        for result in results:
            if result.is_violation:
                violation = Violation(
                    element_name=result.element.name,
                    element_type=result.element.element_type,
                    voltage_level=result.element.voltage_level,
                    region=result.element.region,
                    analysis_type=result.analysis_type,
                    violation_value=result.value,
                    limit_value=result.limit,
                    severity=self._calculate_severity(result),
                    scenario=scenario,
                    timestamp=result.timestamp,
                    metadata=result.metadata.copy()
                )
                violations.append(violation)
        
        return violations
    
    def _calculate_severity(self, result: AnalysisResult) -> str:
        """Calculate violation severity."""
        if result.analysis_type == AnalysisType.THERMAL:
            # Thermal violations
            percent_over_limit = ((result.value - result.limit) / result.limit) * 100
            if percent_over_limit > 20:
                return "Critical"
            elif percent_over_limit > 10:
                return "High"
            elif percent_over_limit > 5:
                return "Medium"
            else:
                return "Low"
        
        elif result.analysis_type == AnalysisType.VOLTAGE:
            # Voltage violations
            if result.metadata.get('violation_type') == 'undervoltage':
                deviation = abs(result.limit - result.value)
            else:
                deviation = abs(result.value - result.limit)
            
            if deviation > 0.05:  # > 5% deviation
                return "Critical"
            elif deviation > 0.03:  # > 3% deviation
                return "High"
            elif deviation > 0.02:  # > 2% deviation
                return "Medium"
            else:
                return "Low"
        
        return "Medium"
    
    def get_violations_by_type(self, analysis_type: AnalysisType) -> List[Violation]:
        """Get violations filtered by analysis type."""
        all_violations = self.get_all_violations()
        return [v for v in all_violations if v.analysis_type == analysis_type]
    
    def get_violations_by_region(self, region: Region) -> List[Violation]:
        """Get violations filtered by region."""
        all_violations = self.get_all_violations()
        return [v for v in all_violations if v.region == region]
    
    def get_violations_by_voltage_level(self, voltage_level: float) -> List[Violation]:
        """Get violations filtered by voltage level."""
        all_violations = self.get_all_violations()
        return [v for v in all_violations if v.voltage_level == voltage_level]
    
    def get_violations_by_severity(self, severity: str) -> List[Violation]:
        """Get violations filtered by severity."""
        all_violations = self.get_all_violations()
        return [v for v in all_violations if v.severity == severity]
    
    def get_critical_violations(self) -> List[Violation]:
        """Get only critical violations."""
        return self.get_violations_by_severity("Critical")
    
    def get_contingency_violations(self) -> Dict[str, List[Violation]]:
        """Get violations grouped by contingency."""
        violations_by_contingency = {}
        
        for contingency_name, contingency_data in self.contingency_results.items():
            contingency_violations = []
            
            for analysis_type, results in contingency_data.items():
                violations = self._extract_violations(results, contingency_name, analysis_type)
                contingency_violations.extend(violations)
            
            violations_by_contingency[contingency_name] = contingency_violations
        
        return violations_by_contingency
    
    def get_worst_contingencies(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get worst contingencies ranked by number of violations.
        
        Args:
            top_n: Number of worst contingencies to return
            
        Returns:
            List of contingency summaries sorted by violation count
        """
        contingency_violations = self.get_contingency_violations()
        
        contingency_summary = []
        for contingency_name, violations in contingency_violations.items():
            if violations:  # Only include contingencies with violations
                critical_count = len([v for v in violations if v.severity == "Critical"])
                high_count = len([v for v in violations if v.severity == "High"])
                
                summary = {
                    'contingency_name': contingency_name,
                    'total_violations': len(violations),
                    'critical_violations': critical_count,
                    'high_violations': high_count,
                    'thermal_violations': len([v for v in violations if v.analysis_type == AnalysisType.THERMAL]),
                    'voltage_violations': len([v for v in violations if v.analysis_type == AnalysisType.VOLTAGE])
                }
                contingency_summary.append(summary)
        
        # Sort by total violations (descending), then by critical violations
        contingency_summary.sort(key=lambda x: (x['total_violations'], x['critical_violations']), reverse=True)
        
        return contingency_summary[:top_n]
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        if self._summary_statistics is not None:
            return self._summary_statistics
        
        all_violations = self.get_all_violations()
        
        # Basic counts
        stats = {
            'total_violations': len(all_violations),
            'base_case_violations': len([v for v in all_violations if v.scenario == "Base Case"]),
            'contingency_violations': len([v for v in all_violations if v.scenario != "Base Case"]),
            'thermal_violations': len([v for v in all_violations if v.analysis_type == AnalysisType.THERMAL]),
            'voltage_violations': len([v for v in all_violations if v.analysis_type == AnalysisType.VOLTAGE])
        }
        
        # Severity breakdown
        stats['severity_breakdown'] = {
            'critical': len([v for v in all_violations if v.severity == "Critical"]),
            'high': len([v for v in all_violations if v.severity == "High"]),
            'medium': len([v for v in all_violations if v.severity == "Medium"]),
            'low': len([v for v in all_violations if v.severity == "Low"])
        }
        
        # Regional breakdown
        stats['regional_breakdown'] = {
            'scotland': len([v for v in all_violations if v.region == Region.SCOTLAND]),
            'england': len([v for v in all_violations if v.region == Region.ENGLAND])
        }
        
        # Voltage level breakdown
        voltage_levels = set(v.voltage_level for v in all_violations)
        stats['voltage_level_breakdown'] = {
            f"{level}kV": len([v for v in all_violations if v.voltage_level == level])
            for level in voltage_levels
        }
        
        # Contingency statistics
        contingency_violations = self.get_contingency_violations()
        contingencies_with_violations = len([c for c, v in contingency_violations.items() if v])
        total_contingencies = len(self.contingency_results)
        
        stats['contingency_statistics'] = {
            'total_contingencies_analyzed': total_contingencies,
            'contingencies_with_violations': contingencies_with_violations,
            'contingency_violation_rate': (contingencies_with_violations / total_contingencies * 100) if total_contingencies > 0 else 0
        }
        
        # Element statistics
        violated_elements = set(v.element_name for v in all_violations)
        stats['element_statistics'] = {
            'unique_violated_elements': len(violated_elements),
            'worst_performing_elements': self._get_worst_elements(all_violations)
        }
        
        self._summary_statistics = stats
        return stats
    
    def _get_worst_elements(self, violations: List[Violation], top_n: int = 10) -> List[Dict[str, Any]]:
        """Get elements with most violations."""
        element_counts = {}
        
        for violation in violations:
            if violation.element_name not in element_counts:
                element_counts[violation.element_name] = {
                    'element_name': violation.element_name,
                    'element_type': violation.element_type.value,
                    'voltage_level': violation.voltage_level,
                    'region': violation.region.value,
                    'violation_count': 0,
                    'critical_count': 0
                }
            
            element_counts[violation.element_name]['violation_count'] += 1
            if violation.severity == "Critical":
                element_counts[violation.element_name]['critical_count'] += 1
        
        # Sort by violation count
        worst_elements = list(element_counts.values())
        worst_elements.sort(key=lambda x: (x['violation_count'], x['critical_count']), reverse=True)
        
        return worst_elements[:top_n]
    
    def get_asset_loading_summary(self) -> Dict[str, Any]:
        """Get summary of asset loading from thermal analysis."""
        thermal_results = []
        
        # Collect all thermal results
        thermal_results.extend(self.base_case_results.get('thermal', []))
        
        for contingency_data in self.contingency_results.values():
            thermal_results.extend(contingency_data.get('thermal', []))
        
        if not thermal_results:
            return {}
        
        # Calculate statistics
        loadings = [r.value for r in thermal_results]
        
        summary = {
            'total_elements': len(thermal_results),
            'max_loading': max(loadings),
            'min_loading': min(loadings),
            'avg_loading': sum(loadings) / len(loadings),
            'elements_over_90': len([l for l in loadings if l > 90]),
            'elements_over_100': len([l for l in loadings if l > 100]),
        }
        
        # Loading distribution
        summary['loading_distribution'] = {
            '0-50%': len([l for l in loadings if 0 <= l < 50]),
            '50-75%': len([l for l in loadings if 50 <= l < 75]),
            '75-90%': len([l for l in loadings if 75 <= l < 90]),
            '90-100%': len([l for l in loadings if 90 <= l <= 100]),
            '>100%': len([l for l in loadings if l > 100])
        }
        
        return summary
    
    def get_voltage_profile_summary(self) -> Dict[str, Any]:
        """Get summary of voltage profiles from voltage analysis."""
        voltage_results = []
        
        # Collect all voltage results
        voltage_results.extend(self.base_case_results.get('voltage', []))
        
        for contingency_data in self.contingency_results.values():
            voltage_results.extend(contingency_data.get('voltage', []))
        
        if not voltage_results:
            return {}
        
        # Calculate statistics
        voltages = [r.value for r in voltage_results]
        
        summary = {
            'total_buses': len(voltage_results),
            'max_voltage': max(voltages),
            'min_voltage': min(voltages),
            'avg_voltage': sum(voltages) / len(voltages),
            'buses_under_95': len([v for v in voltages if v < 0.95]),
            'buses_over_105': len([v for v in voltages if v > 1.05]),
        }
        
        # Voltage distribution
        summary['voltage_distribution'] = {
            '<0.95 pu': len([v for v in voltages if v < 0.95]),
            '0.95-0.97 pu': len([v for v in voltages if 0.95 <= v < 0.97]),
            '0.97-1.03 pu': len([v for v in voltages if 0.97 <= v <= 1.03]),
            '1.03-1.05 pu': len([v for v in voltages if 1.03 < v <= 1.05]),
            '>1.05 pu': len([v for v in voltages if v > 1.05])
        }
        
        return summary
    
    def export_results_to_dict(self) -> Dict[str, Any]:
        """Export all results to dictionary format."""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'summary_statistics': self.get_summary_statistics(),
            'violations': [v.to_dict() for v in self.get_all_violations()],
            'asset_loading_summary': self.get_asset_loading_summary(),
            'voltage_profile_summary': self.get_voltage_profile_summary(),
            'worst_contingencies': self.get_worst_contingencies(),
            'base_case_results': self._serialize_results(self.base_case_results),
            'contingency_results': {
                name: self._serialize_results(data) 
                for name, data in self.contingency_results.items()
            }
        }
        
        return export_data
    
    def _serialize_results(self, results: Dict[str, List[AnalysisResult]]) -> Dict[str, List[Dict[str, Any]]]:
        """Serialize analysis results to dictionary format."""
        serialized = {}
        
        for analysis_type, result_list in results.items():
            serialized[analysis_type] = [r.to_dict() for r in result_list]
        
        return serialized
    
    def save_results_to_json(self, filepath: Union[str, Path]) -> bool:
        """
        Save results to JSON file.
        
        Args:
            filepath: Path to output JSON file
            
        Returns:
            True if successful
        """
        try:
            export_data = self.export_results_to_dict()
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Results exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save results to JSON: {e}")
            return False
    
    def _clear_cache(self) -> None:
        """Clear processed results cache."""
        self._processed_violations = None
        self._summary_statistics = None
    
    def clear_all_results(self) -> None:
        """Clear all stored results."""
        self.base_case_results.clear()
        self.contingency_results.clear()
        self._clear_cache()
        self.logger.info("All results cleared")
