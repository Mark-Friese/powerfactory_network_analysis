# Scottish 33kV Distribution Network Contingency Analysis Guide

## Overview

This guide shows you how to use your existing PowerFactory analysis framework to run comprehensive contingency analysis for Scottish distribution networks, specifically focusing on BESS export/import scenarios and their impact during asset outages.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setup and Configuration](#setup-and-configuration)
3. [Running Glenrothes BESS Analysis](#running-glenrothes-bess-analysis)
4. [Understanding Results](#understanding-results)
5. [Customization](#customization)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### New Files Added

Your framework has been enhanced with three new files:

- `src/core/scenario_manager.py` - Handles BESS scenario management
- `scripts/run_glenrothes_analysis.py` - Glenrothes-specific analysis script
- `config/glenrothes_analysis.yaml` - Configuration template for Scottish networks

### Basic Analysis

```bash
# Quick analysis with default settings
python scripts/run_glenrothes_analysis.py

# Test configuration without running analysis
python scripts/run_glenrothes_analysis.py --dry-run
```

## Setup and Configuration

### 1. Update Asset Names

Edit `config/glenrothes_analysis.yaml` to match your PowerFactory model:

```yaml
scenarios:
  bess_elements:
    bess_a: "YOUR_ACTUAL_BESS_A_NAME"    # Replace with actual name
    bess_b: "YOUR_ACTUAL_BESS_B_NAME"    # Replace with actual name

contingencies:
  priority_assets:
    # Update these patterns to match your naming convention
    - pattern: "*Glenrothes*33/11*"
      type: "ElmTr2"
      description: "Primary transformers"
    
    - pattern: "*Glenrothes*33kV*Feeder*"
      type: "ElmLne"
      description: "33kV feeders"
```

### 2. Verify Configuration

```bash
# Validate your configuration
python scripts/run_glenrothes_analysis.py --dry-run
```

If the dry run fails, check:

- BESS names exist in your PowerFactory model
- Asset naming patterns match your network
- PowerFactory is accessible

## Running Glenrothes BESS Analysis

### Standard Analysis

```bash
# Run with your specific BESS names
python scripts/run_glenrothes_analysis.py \
  --bess-a-name "Glenrothes_BESS_East" \
  --bess-b-name "Glenrothes_BESS_West"

# Limit number of contingencies for faster testing
python scripts/run_glenrothes_analysis.py --max-contingencies 20

# Custom area pattern and output location
python scripts/run_glenrothes_analysis.py \
  --area-pattern "Glenrothes*" \
  --output-dir ./my_results
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--bess-a-name` | Name of first BESS unit | Glenrothes_BESS_A |
| `--bess-b-name` | Name of second BESS unit | Glenrothes_BESS_B |
| `--area-pattern` | Pattern to filter network elements | Glenrothes* |
| `--max-contingencies` | Maximum contingencies per scenario | 50 |
| `--output-dir` | Output directory | ./output/glenrothes |
| `--dry-run` | Test setup without running analysis | false |
| `--log-level` | Logging detail level | INFO |

### What the Analysis Does

The script automatically:

1. **Creates BESS Scenarios**: Tests combinations where:
   - BESS A is always at 100% export
   - BESS B varies from 100% export to 100% import in steps

2. **Identifies Priority Assets**: Finds:
   - 33/11kV primary transformers
   - 33kV primary feeder circuits
   - Bus-section equipment (switches, reactors)

3. **Runs Contingency Analysis**: For each BESS scenario:
   - Runs base case load flow
   - Tests each priority asset outage
   - Records thermal and voltage violations

4. **Generates Reports**: Creates summary analysis showing:
   - Worst-case BESS combinations
   - Critical contingencies
   - Violation patterns

## Understanding Results

### Output Files

After analysis, you'll find in the output directory:

```
analysis_YYYYMMDD_HHMMSS/
├── analysis_summary.csv          # Key findings summary
├── detailed_results.yaml         # Complete scenario results
└── logs/                          # Detailed execution logs
```

### Key Metrics in Summary Report

| Column | Description |
|--------|-------------|
| Scenario | BESS A/B export/import combination |
| Base_Thermal_Violations | Violations without any outages |
| Base_Voltage_Violations | Voltage violations in base case |
| Worst_Contingency | Asset outage causing most violations |
| Max_Contingency_Violations | Highest violation count |
| Critical_Contingencies | Number of outages causing >5 violations |

### Interpreting Results

**Worst-Case Scenarios**: Look for scenarios with:

- High base case violations (network already stressed)
- High contingency violations (poor resilience)
- Many critical contingencies (multiple problematic outages)

**Key Insights**: The analysis helps identify:

- BESS combinations that overload the bus-section reactor
- Primary transformers most affected by unbalanced flows
- Operating patterns with low resilience to outages
- Whether certain BESS combinations are operationally unrealistic

## Customization

### Adding More Scenarios

Edit `config/glenrothes_analysis.yaml` to add custom scenarios:

```yaml
scenarios:
  custom_scenarios:
    - name: "High_Wind_Low_Load"
      description: "High wind generation with low demand"
      elements:
        - name: "Glenrothes_Wind_Farm"
          type: "ElmGenstat"
          scaling_factor: 0.9
      load_scaling: 0.4
```

### Changing Analysis Focus

**For Different Asset Types**: Update the `priority_assets` patterns in the config file.

**For Different Areas**: Use the `--area-pattern` option or modify the config file.

**For Different Voltage Levels**: Adjust the `voltage_limits` in the configuration.

### Additional BESS Units

To analyze more than 2 BESS units, modify the scenario creation in `scenario_manager.py` or add custom scenarios to the configuration file.

## Troubleshooting

### Common Issues

**1. "BESS not found" errors**

- Check BESS names exactly match PowerFactory model
- Verify BESS units are modeled as `ElmGenstat` objects
- Use PowerFactory browser to confirm exact names

**2. "No elements found for area pattern"**

- Check if your naming convention uses "Glenrothes"
- Try broader patterns like "*Glen*" or "*rothes*"
- List all elements first with the main analysis script

**3. "Load flow failed"**

- Some BESS combinations may create unsolvable conditions
- Check PowerFactory load flow settings
- Review base case before adding scenarios

**4. "No contingency assets identified"**

- Verify asset naming patterns in configuration
- Check voltage level filtering (minimum 11kV by default)
- Ensure assets are in service in PowerFactory

### Debug Mode

```bash
# Enable detailed logging
python scripts/run_glenrothes_analysis.py --log-level DEBUG

# Check what elements are found
python scripts/run_analysis.py --config config/glenrothes_analysis.yaml --base-case-only
```

### Getting Help

1. **Check Log Files**: Detailed execution logs are saved in the output directory
2. **Validate Configuration**: Use `--dry-run` to test setup without running analysis
3. **Review PowerFactory Model**: Ensure all referenced assets exist and are properly named
4. **Test Base Case**: Run base case analysis first to verify PowerFactory connectivity

## Next Steps

Once you have results:

1. **Identify Worst-Case Scenarios**: Focus on combinations with highest violation counts
2. **Assess Operational Probability**: Consider how likely problematic scenarios are in practice
3. **Plan Reinforcements**: Target critical contingencies that cause multiple violations
4. **Operational Guidelines**: Develop BESS operating constraints based on findings
5. **Iterative Analysis**: Refine scenarios based on operational experience

The analysis provides quantitative evidence for:

- Network reinforcement business cases
- BESS operational constraints
- Discussion with generation operators about realistic operating patterns
- Understanding the impact of the bus-section reactor on network flows

This data-driven approach helps balance network security with operational flexibility for your Scottish distribution network.
