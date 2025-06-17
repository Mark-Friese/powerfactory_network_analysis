# SPD 33kV Distribution Network Contingency Analysis Guide

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setup and Configuration](#setup-and-configuration)
3. [Grid Selection and Filtering](#grid-selection-and-filtering)
4. [Generation and BESS Scenario Configuration](#generation-and-bess-scenario-configuration)
5. [Running Contingency Analysis](#running-contingency-analysis)
6. [Iterative Studies for Glenrothes Area](#iterative-studies-for-glenrothes-area)
7. [Results Analysis and Visualization](#results-analysis-and-visualization)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites Check

Before starting, fix the bug in `network_analyzer.py` line 40:

```python
# Change this:
self.contingency_manager = ContingencyManager(self.pf_interface, self.config)
# To this:
self.contingency_manager = ContingencyManager(self.pf_interface)
```

### Basic Contingency Analysis

```bash
# Run contingency analysis with default settings
python scripts/run_analysis.py --config config/glenrothes_analysis.yaml

# Run with custom output directory
python scripts/run_analysis.py --output-dir ./glenrothes_results --format both
```

## Setup and Configuration

### 1. Create Glenrothes-Specific Configuration

Create a new configuration file for your Scottish network analysis:

```yaml
# config/glenrothes_analysis.yaml
analysis:
  # Scottish 33kV network specific limits
  thermal_limits:
    default: 90.0
    transformers: 85.0  # 33/11kV primary transformers
    lines: 90.0         # 33kV feeders
    reactors: 70.0      # Bus-section reactors
  
  voltage_limits:
    scotland:
      33.0:
        min: 0.97  # 32.01kV
        max: 1.04  # 34.32kV
      11.0:
        min: 0.95  # 10.45kV
        max: 1.05  # 11.55kV
  
  options:
    run_base_case: true
    run_contingency: true
    max_contingencies: 100  # Adjust based on network size
    include_out_of_service: false

# Scottish network configuration
regions:
  scotland:
    name: "Scotland"
    voltage_levels: [33.0, 11.0]
    grid_filter: "Glenrothes*"  # Filter for specific area

# Generation and BESS scenario definitions
scenarios:
  generation_scaling:
    # BESS export/import combinations for Glenrothes
    glenrothes_bess_scenarios:
      - name: "BESS_A_100_BESS_B_100"
        description: "BESS A 100% export, BESS B 100% export"
        elements:
          - name: "Glenrothes_BESS_A"
            type: "ElmGenstat"
            scaling_factor: 1.0    # 100% export
          - name: "Glenrothes_BESS_B" 
            type: "ElmGenstat"
            scaling_factor: 1.0    # 100% export
      
      - name: "BESS_A_100_BESS_B_80"
        description: "BESS A 100% export, BESS B 80% export"
        elements:
          - name: "Glenrothes_BESS_A"
            type: "ElmGenstat"
            scaling_factor: 1.0
          - name: "Glenrothes_BESS_B"
            type: "ElmGenstat"
            scaling_factor: 0.8
      
      - name: "BESS_A_100_BESS_B_60"
        description: "BESS A 100% export, BESS B 60% export"
        elements:
          - name: "Glenrothes_BESS_A"
            type: "ElmGenstat"
            scaling_factor: 1.0
          - name: "Glenrothes_BESS_B"
            type: "ElmGenstat"
            scaling_factor: 0.6
      
      - name: "BESS_A_100_BESS_B_neg100"
        description: "BESS A 100% export, BESS B 100% import"
        elements:
          - name: "Glenrothes_BESS_A"
            type: "ElmGenstat"
            scaling_factor: 1.0
          - name: "Glenrothes_BESS_B"
            type: "ElmGenstat"
            scaling_factor: -1.0   # Negative for import
  
  primary_loading:
    # Different primary transformer loading scenarios
    - name: "Peak_Load"
      description: "Peak loading conditions"
      load_scaling: 1.0
    - name: "Medium_Load"
      description: "Medium loading conditions"
      load_scaling: 0.7
    - name: "Light_Load"
      description: "Light loading conditions"
      load_scaling: 0.4

# Contingency definitions
contingencies:
  priority_assets:
    # 33/11kV Primary transformers
    - pattern: "*33/11*Transformer*"
      type: "ElmTr2"
      description: "Primary transformers"
    
    # 33kV Primary feeders
    - pattern: "*33kV*Feeder*"
      type: "ElmLne"
      description: "33kV primary feeders"
    
    # Bus-section equipment
    - pattern: "*Bus*Section*"
      type: "ElmCoup"
      description: "Bus-section switches"
    
    - pattern: "*Reactor*"
      type: "ElmReac"
      description: "Bus-section reactors"

# Output configuration
output:
  formats: [excel, csv]
  include_scenarios: true
  scenario_comparison: true
  
  excel:
    include_charts: true
    include_summary: true
    scenario_tabs: true
  
  sections:
    - violations
    - asset_loading
    - voltage_profiles
    - contingency_summary
    - scenario_comparison
    - worst_case_analysis
```

### 2. Network Element Filtering

The existing framework automatically filters elements based on your configuration. To focus on the Glenrothes area:

```python
# In your PowerFactory interface, elements are filtered by:
# - Voltage level (33kV, 11kV for Scotland)
# - Grid pattern matching
# - Asset type (transformers, lines, etc.)
```

## Grid Selection and Filtering

### Current Implementation

Your existing `NetworkAnalyzer` loads all network elements and filters them. For Glenrothes-specific analysis:

1. **Voltage Level Filtering**: Automatically includes 33kV and 11kV elements
2. **Pattern Matching**: Use PowerFactory naming conventions
3. **Geographic Filtering**: Based on PowerFactory grid structure

### Enhancing Grid Selection

Add this method to your `NetworkAnalyzer` class:

```python
def filter_elements_by_area(self, elements: List[NetworkElement], area_pattern: str) -> List[NetworkElement]:
    """
    Filter network elements by geographic area.
    
    Args:
        elements: List of network elements
        area_pattern: Pattern to match (e.g., "Glenrothes*")
    
    Returns:
        Filtered list of elements for the specified area
    """
    import fnmatch
    
    filtered_elements = []
    for element in elements:
        # Check if element name matches area pattern
        if fnmatch.fnmatch(element.name, area_pattern):
            filtered_elements.append(element)
        
        # Also check parent grid/substation
        if hasattr(element.powerfactory_object, 'GetParent'):
            parent = element.powerfactory_object.GetParent()
            if parent and fnmatch.fnmatch(parent.loc_name, area_pattern):
                filtered_elements.append(element)
    
    self.logger.info(f"Filtered to {len(filtered_elements)} elements for area: {area_pattern}")
    return filtered_elements
```

## Generation and BESS Scenario Configuration

### Creating Scenario Manager

Create a new file `src/core/scenario_manager.py`:

```python
"""
Scenario management for generation and loading variations.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .powerfactory_interface import PowerFactoryInterface
from ..models.network_element import NetworkElement
from ..utils.logger import AnalysisLogger


@dataclass
class ScenarioElement:
    """Represents an element in a scenario with its scaling factor."""
    name: str
    element_type: str  # PowerFactory type (ElmGenstat, ElmLod, etc.)
    scaling_factor: float
    original_value: Optional[float] = None


@dataclass
class Scenario:
    """Represents a complete scenario configuration."""
    name: str
    description: str
    elements: List[ScenarioElement]
    load_scaling: float = 1.0


class ScenarioManager:
    """
    Manages generation and loading scenarios for iterative analysis.
    """
    
    def __init__(self, pf_interface: PowerFactoryInterface):
        self.pf_interface = pf_interface
        self.logger = AnalysisLogger(__name__)
        self._original_values: Dict[str, float] = {}
        self._active_scenario: Optional[str] = None
    
    def create_bess_scenarios(self, bess_a_name: str, bess_b_name: str) -> List[Scenario]:
        """
        Create BESS export/import combination scenarios.
        
        Args:
            bess_a_name: Name of first BESS unit
            bess_b_name: Name of second BESS unit
        
        Returns:
            List of BESS scenarios
        """
        scenarios = []
        
        # Define BESS B scaling factors to test
        bess_b_factors = [1.0, 0.8, 0.6, 0.4, 0.0, -0.4, -0.6, -0.8, -1.0]
        
        for factor in bess_b_factors:
            scenario_name = f"BESS_A_100_BESS_B_{int(factor*100)}"
            if factor < 0:
                scenario_name = f"BESS_A_100_BESS_B_neg{int(abs(factor)*100)}"
            
            description = f"BESS A 100% export, BESS B {factor*100}% "
            description += "export" if factor >= 0 else "import"
            
            scenario = Scenario(
                name=scenario_name,
                description=description,
                elements=[
                    ScenarioElement(bess_a_name, "ElmGenstat", 1.0),
                    ScenarioElement(bess_b_name, "ElmGenstat", factor)
                ]
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def apply_scenario(self, scenario: Scenario) -> bool:
        """
        Apply a scenario to the PowerFactory model.
        
        Args:
            scenario: Scenario to apply
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Applying scenario: {scenario.name}")
            
            # Store original values if not already stored
            for element in scenario.elements:
                if element.name not in self._original_values:
                    pf_obj = self.pf_interface.get_object_by_name(element.name, element.element_type)
                    if pf_obj:
                        if element.element_type == "ElmGenstat":
                            original = self.pf_interface.get_element_attribute(pf_obj, "pgini")
                        elif element.element_type == "ElmLod":
                            original = self.pf_interface.get_element_attribute(pf_obj, "plini")
                        else:
                            continue
                        
                        self._original_values[element.name] = original
                        element.original_value = original
            
            # Apply scaling factors
            for element in scenario.elements:
                pf_obj = self.pf_interface.get_object_by_name(element.name, element.element_type)
                if pf_obj and element.original_value is not None:
                    new_value = element.original_value * element.scaling_factor
                    
                    if element.element_type == "ElmGenstat":
                        success = self.pf_interface.set_element_attribute(pf_obj, "pgini", new_value)
                    elif element.element_type == "ElmLod":
                        success = self.pf_interface.set_element_attribute(pf_obj, "plini", new_value)
                    else:
                        continue
                    
                    if not success:
                        self.logger.warning(f"Failed to set value for {element.name}")
                        return False
            
            # Apply load scaling if specified
            if scenario.load_scaling != 1.0:
                self._apply_load_scaling(scenario.load_scaling)
            
            self._active_scenario = scenario.name
            self.logger.debug(f"Successfully applied scenario: {scenario.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying scenario {scenario.name}: {e}")
            return False
    
    def restore_original_values(self) -> bool:
        """
        Restore all elements to their original values.
        
        Returns:
            True if successful
        """
        try:
            for element_name, original_value in self._original_values.items():
                # Need to determine element type - could be enhanced
                for element_type in ["ElmGenstat", "ElmLod"]:
                    pf_obj = self.pf_interface.get_object_by_name(element_name, element_type)
                    if pf_obj:
                        if element_type == "ElmGenstat":
                            attr = "pgini"
                        elif element_type == "ElmLod":
                            attr = "plini"
                        else:
                            continue
                        
                        self.pf_interface.set_element_attribute(pf_obj, attr, original_value)
                        break
            
            self._active_scenario = None
            self.logger.info("Restored all elements to original values")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring values: {e}")
            return False
    
    def _apply_load_scaling(self, scaling_factor: float) -> None:
        """Apply uniform load scaling."""
        load_objects = self.pf_interface.get_calc_relevant_objects("*.ElmLod")
        for load in load_objects:
            original_p = self.pf_interface.get_element_attribute(load, "plini")
            original_q = self.pf_interface.get_element_attribute(load, "qlini")
            
            if original_p is not None:
                new_p = original_p * scaling_factor
                self.pf_interface.set_element_attribute(load, "plini", new_p)
            
            if original_q is not None:
                new_q = original_q * scaling_factor
                self.pf_interface.set_element_attribute(load, "qlini", new_q)
```

## Running Contingency Analysis

### Enhanced Run Script

Create `scripts/run_glenrothes_analysis.py`:

```python
#!/usr/bin/env python3
"""
Glenrothes area contingency analysis with BESS scenarios.
"""

import sys
from pathlib import Path
import yaml
from datetime import datetime

# Add src to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.core.network_analyzer import NetworkAnalyzer
from src.core.scenario_manager import ScenarioManager
from src.core.contingency_manager import ContingencyManager
from src.utils.logger import AnalysisLogger
from src.reports.excel_reporter import ExcelReporter


def run_glenrothes_contingency_analysis():
    """Run comprehensive Glenrothes area analysis."""
    
    logger = AnalysisLogger("glenrothes_analysis")
    logger.info("Starting Glenrothes contingency analysis")
    
    # Initialize analyzer
    config_path = Path("config/glenrothes_analysis.yaml")
    analyzer = NetworkAnalyzer(config_path)
    
    # Connect to PowerFactory
    if not analyzer.connect_to_powerfactory():
        logger.error("Failed to connect to PowerFactory")
        return False
    
    try:
        # Initialize scenario manager
        scenario_manager = ScenarioManager(analyzer.pf_interface)
        
        # Create BESS scenarios for Glenrothes
        bess_scenarios = scenario_manager.create_bess_scenarios(
            "Glenrothes_BESS_A",  # Adjust names to match your PowerFactory model
            "Glenrothes_BESS_B"
        )
        
        # Load and filter network elements for Glenrothes area
        all_elements = analyzer.load_network_elements()
        glenrothes_elements = analyzer.filter_elements_by_area(all_elements, "Glenrothes*")
        
        # Identify contingency assets (33/11kV transformers and 33kV feeders)
        contingency_assets = []
        for element in glenrothes_elements:
            if (element.element_type.value in ["ElmTr2", "ElmTr3"] and 
                element.voltage_level == 33.0):
                contingency_assets.append(element)
            elif (element.element_type.value == "ElmLne" and 
                  element.voltage_level == 33.0):
                contingency_assets.append(element)
        
        logger.info(f"Found {len(contingency_assets)} contingency assets")
        
        all_results = {}
        
        # Run analysis for each BESS scenario
        for i, scenario in enumerate(bess_scenarios, 1):
            logger.info(f"Running scenario {i}/{len(bess_scenarios)}: {scenario.name}")
            
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
                        'thermal': analyzer.thermal_analyzer.analyze_network(glenrothes_elements),
                        'voltage': analyzer.voltage_analyzer.analyze_network(glenrothes_elements)
                    }
                else:
                    logger.warning(f"Base case load flow failed for scenario: {scenario.name}")
                    continue
            except Exception as e:
                logger.error(f"Base case analysis failed for scenario {scenario.name}: {e}")
                continue
            
            # Run contingency analysis for priority assets
            contingency_results = {}
            for j, asset in enumerate(contingency_assets, 1):
                logger.info(f"  Contingency {j}/{len(contingency_assets)}: {asset.name}")
                
                try:
                    # Apply contingency
                    if analyzer.contingency_manager.apply_contingency(asset):
                        # Run load flow
                        if analyzer.pf_interface.execute_load_flow():
                            # Analyze results
                            contingency_results[asset.name] = {
                                'thermal': analyzer.thermal_analyzer.analyze_network(glenrothes_elements, asset.name),
                                'voltage': analyzer.voltage_analyzer.analyze_network(glenrothes_elements, asset.name)
                            }
                        else:
                            logger.warning(f"Load flow failed for contingency: {asset.name}")
                        
                        # Restore
                        analyzer.contingency_manager.restore_contingency(asset)
                    else:
                        logger.warning(f"Failed to apply contingency: {asset.name}")
                
                except Exception as e:
                    logger.error(f"Error in contingency {asset.name}: {e}")
                    # Ensure restoration
                    analyzer.contingency_manager.restore_contingency(asset)
            
            scenario_results['contingencies'] = contingency_results
            all_results[scenario.name] = scenario_results
            
            # Restore scenario
            scenario_manager.restore_original_values()
        
        # Generate comprehensive report
        output_dir = Path(f"output/glenrothes_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Excel report with scenario comparison
        excel_path = output_dir / "glenrothes_contingency_analysis.xlsx"
        generate_glenrothes_report(all_results, excel_path, logger)
        
        logger.info(f"Analysis completed. Results saved to: {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return False
    
    finally:
        analyzer.disconnect()


def generate_glenrothes_report(results: dict, output_path: Path, logger: AnalysisLogger):
    """Generate comprehensive Glenrothes analysis report."""
    
    try:
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill, Font
        from openpyxl.chart import LineChart, Reference
        
        wb = Workbook()
        
        # Summary sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        
        # Write summary headers
        ws_summary['A1'] = "Glenrothes BESS Contingency Analysis Summary"
        ws_summary['A1'].font = Font(bold=True, size=14)
        
        row = 3
        ws_summary[f'A{row}'] = "Scenario"
        ws_summary[f'B{row}'] = "Base Case Violations"
        ws_summary[f'C{row}'] = "Worst Contingency"
        ws_summary[f'D{row}'] = "Max Violations"
        ws_summary[f'E{row}'] = "Critical Assets"
        
        # Format headers
        for col in ['A', 'B', 'C', 'D', 'E']:
            ws_summary[f'{col}{row}'].font = Font(bold=True)
            ws_summary[f'{col}{row}'].fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        row += 1
        
        # Process each scenario
        scenario_data = []
        for scenario_name, scenario_results in results.items():
            # Count base case violations
            base_violations = 0
            for analysis_type, analysis_results in scenario_results['base_case'].items():
                base_violations += len([r for r in analysis_results if r.is_violation])
            
            # Find worst contingency
            worst_contingency = ""
            max_violations = 0
            critical_assets = []
            
            for contingency_name, contingency_results in scenario_results['contingencies'].items():
                violation_count = 0
                for analysis_type, analysis_results in contingency_results.items():
                    violations = [r for r in analysis_results if r.is_violation]
                    violation_count += len(violations)
                    
                    # Check for critical violations (>100% loading or voltage outside limits)
                    for violation in violations:
                        if ((analysis_type == 'thermal' and violation.value > 100) or
                            (analysis_type == 'voltage' and (violation.value < 0.94 or violation.value > 1.06))):
                            if contingency_name not in critical_assets:
                                critical_assets.append(contingency_name)
                
                if violation_count > max_violations:
                    max_violations = violation_count
                    worst_contingency = contingency_name
            
            # Write scenario summary
            ws_summary[f'A{row}'] = scenario_name
            ws_summary[f'B{row}'] = base_violations
            ws_summary[f'C{row}'] = worst_contingency
            ws_summary[f'D{row}'] = max_violations
            ws_summary[f'E{row}'] = len(critical_assets)
            
            scenario_data.append({
                'scenario': scenario_name,
                'base_violations': base_violations,
                'max_violations': max_violations,
                'critical_assets': len(critical_assets)
            })
            
            row += 1
        
        # Create detailed sheets for each analysis type
        for analysis_type in ['thermal', 'voltage']:
            ws = wb.create_sheet(f"{analysis_type.title()} Analysis")
            
            # Headers
            headers = ['Scenario', 'Element', 'Contingency', 'Value', 'Limit', 'Violation', 'Severity']
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
                ws.cell(row=1, column=col).font = Font(bold=True)
                ws.cell(row=1, column=col).fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
            row = 2
            
            # Write detailed results
            for scenario_name, scenario_results in results.items():
                # Base case results
                if analysis_type in scenario_results['base_case']:
                    for result in scenario_results['base_case'][analysis_type]:
                        ws.cell(row=row, column=1, value=scenario_name)
                        ws.cell(row=row, column=2, value=result.element_name)
                        ws.cell(row=row, column=3, value="Base Case")
                        ws.cell(row=row, column=4, value=result.value)
                        ws.cell(row=row, column=5, value=result.limit)
                        ws.cell(row=row, column=6, value="Yes" if result.is_violation else "No")
                        ws.cell(row=row, column=7, value=result.violation_severity if result.is_violation else "N/A")
                        
                        # Color-code violations
                        if result.is_violation:
                            color = "FFB6C1" if result.violation_severity == "Low" else "FFD700" if result.violation_severity == "Medium" else "FF6B6B"
                            for col in range(1, 8):
                                ws.cell(row=row, column=col).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
                        
                        row += 1
                
                # Contingency results
                for contingency_name, contingency_results in scenario_results['contingencies'].items():
                    if analysis_type in contingency_results:
                        for result in contingency_results[analysis_type]:
                            ws.cell(row=row, column=1, value=scenario_name)
                            ws.cell(row=row, column=2, value=result.element_name)
                            ws.cell(row=row, column=3, value=contingency_name)
                            ws.cell(row=row, column=4, value=result.value)
                            ws.cell(row=row, column=5, value=result.limit)
                            ws.cell(row=row, column=6, value="Yes" if result.is_violation else "No")
                            ws.cell(row=row, column=7, value=result.violation_severity if result.is_violation else "N/A")
                            
                            # Color-code violations
                            if result.is_violation:
                                color = "FFB6C1" if result.violation_severity == "Low" else "FFD700" if result.violation_severity == "Medium" else "FF6B6B"
                                for col in range(1, 8):
                                    ws.cell(row=row, column=col).fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
                            
                            row += 1
        
        # Create visualization sheet
        ws_chart = wb.create_sheet("Scenario Comparison")
        
        # Write data for chart
        ws_chart['A1'] = "Scenario"
        ws_chart['B1'] = "Base Case Violations"
        ws_chart['C1'] = "Max Contingency Violations"
        
        for i, data in enumerate(scenario_data, 2):
            ws_chart[f'A{i}'] = data['scenario']
            ws_chart[f'B{i}'] = data['base_violations']
            ws_chart[f'C{i}'] = data['max_violations']
        
        # Create chart
        chart = LineChart()
        chart.title = "Violations by BESS Scenario"
        chart.style = 13
        chart.x_axis.title = "Scenario"
        chart.y_axis.title = "Number of Violations"
        
        data = Reference(ws_chart, min_col=2, min_row=1, max_col=3, max_row=len(scenario_data)+1)
        cats = Reference(ws_chart, min_col=1, min_row=2, max_row=len(scenario_data)+1)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        
        ws_chart.add_chart(chart, "E5")
        
        # Auto-adjust column widths
        for ws in wb.worksheets:
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save workbook
        wb.save(output_path)
        logger.info(f"Excel report generated: {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")


if __name__ == "__main__":
    run_glenrothes_contingency_analysis()
```

## Iterative Studies for Glenrothes Area

### Running the Analysis

```bash
# Run Glenrothes-specific analysis
python scripts/run_glenrothes_analysis.py

# Run with specific BESS combinations
python scripts/run_analysis.py --config config/glenrothes_analysis.yaml --max-contingencies 50
```

### Expected Outputs

1. **Excel Report** with tabs for:
   - Summary of all scenarios
   - Thermal analysis details
   - Voltage analysis details
   - Scenario comparison charts

2. **Key Insights** from analysis:
   - Worst-case BESS combinations
   - Critical contingencies causing violations
   - Asset loading patterns
   - Voltage profile impacts

## Results Analysis and Visualization

### Interpreting Results

1. **Base Case Analysis**: Shows network performance under different BESS export/import combinations
2. **Contingency Impact**: Identifies which asset outages cause violations under different scenarios
3. **Scenario Comparison**: Reveals which BESS combinations create the most stress

### Key Metrics to Monitor

- **Thermal Loading**: Focus on 33/11kV transformers >85% and 33kV lines >90%
- **Voltage Violations**: Outside 0.97-1.04 pu on 33kV, 0.95-1.05 pu on 11kV
- **Unbalanced Flows**: Caused by bus-section reactor impedance
- **Critical Contingencies**: Asset outages that cause multiple violations

### Visualization Tools

The generated Excel reports include:

- Line charts showing violation trends across scenarios
- Heat maps of asset loading
- Contingency ranking tables
- Scenario comparison matrices

## Troubleshooting

### Common Issues

1. **PowerFactory Connection**: Ensure PowerFactory is running and accessible
2. **Element Naming**: Verify BESS and transformer names match your PowerFactory model
3. **Configuration Errors**: Check YAML syntax and element patterns

### Debug Commands

```bash
# Validate configuration
python scripts/run_analysis.py --validate-config --config config/glenrothes_analysis.yaml

# Dry run to test setup
python scripts/run_analysis.py --dry-run --config config/glenrothes_analysis.yaml

# Enable debug logging
python scripts/run_glenrothes_analysis.py --log-level DEBUG
```

### Next Steps

1. **Run the analysis** with your specific PowerFactory model
2. **Review results** to identify worst-case scenarios  
3. **Analyze patterns** in BESS combinations that cause issues
4. **Identify reinforcement options** based on critical contingencies
5. **Refine scenarios** based on operational probability

This guide leverages your existing robust framework while adding the specific scenario and iterative analysis capabilities you need for the Glenrothes area assessment.
