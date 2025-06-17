# PowerFactory Network Analysis Project

## Overview

This project provides a comprehensive automated analysis framework for PowerFactory distribution networks, featuring thermal loading analysis, voltage analysis, and N-1 contingency assessment with regional support for Scotland and England networks.

This project has been fully implemented and is ready for use. All core components, analysis modules, reporting systems, and utilities are complete with comprehensive testing.

## Key Features

- **Automated Thermal Analysis**: Loading analysis for lines, transformers, and cables with configurable limits
- **Voltage Analysis**: Bus voltage analysis with regional and voltage-level specific limits
- **N-1 Contingency Assessment**: Comprehensive contingency analysis with intelligent prioritization
- **Regional Support**: Specialized handling for Scotland (33kV, 11kV) and England (132kV, 33kV, 11kV) networks
- **Multi-Format Reporting**: Excel dashboards with charts and CSV exports for further analysis
- **Batch Processing**: Support for analyzing multiple studies and configurations
- **Comprehensive Logging**: Detailed progress tracking and error reporting
- **Flexible Configuration**: YAML-based configuration with validation

## Architecture Overview

### Core Components

- **NetworkAnalyzer**: Main orchestration class coordinating all analysis workflows
- **PowerFactoryInterface**: Singleton interface managing PowerFactory connections and operations
- **ResultsManager**: Centralized results processing, aggregation, and violation management
- **ContingencyManager**: N-1 contingency scenario management and execution

### Analysis Modules

- **ThermalAnalyzer**: Thermal loading analysis with element-specific limits and severity assessment
- **VoltageAnalyzer**: Voltage analysis with regional limits and violation categorization
- **BaseAnalyzer**: Abstract base providing common analysis patterns and utilities

### Data Models

- **NetworkElement**: Unified representation of PowerFactory network components
- **AnalysisResult**: Standardized analysis result with metadata and status
- **Violation**: Structured violation tracking with severity and contextual information

### Reporting System

- **ExcelReporter**: Rich Excel reports with multiple sheets, formatting, and charts
- **CSVReporter**: Structured CSV exports for data analysis and integration
- **HTMLReporter**: Web-based dashboard reports (future enhancement)

### Utilities

- **FileHandler**: Robust file I/O for YAML, JSON, CSV, and text formats
- **InputValidator**: Comprehensive validation for configurations and inputs
- **AnalysisLogger**: Advanced logging with progress tracking and file management

## Project Structure

```
powerfactory_network_analysis/
├── src/                          # Source code
│   ├── analyzers/               # Analysis modules
│   │   ├── base_analyzer.py     # Abstract base analyzer
│   │   ├── thermal_analyzer.py  # Thermal loading analysis
│   │   └── voltage_analyzer.py  # Voltage analysis
│   ├── core/                    # Core framework
│   │   ├── network_analyzer.py  # Main orchestrator
│   │   ├── powerfactory_interface.py  # PowerFactory API
│   │   ├── results_manager.py   # Results processing
│   │   └── contingency_manager.py  # Contingency management
│   ├── models/                  # Data models
│   │   ├── network_element.py   # Network element representation
│   │   ├── analysis_result.py   # Analysis result model
│   │   └── violation.py         # Violation tracking
│   ├── reports/                 # Report generation
│   │   ├── excel_reporter.py    # Excel report generation
│   │   └── csv_reporter.py      # CSV report generation
│   └── utils/                   # Utilities
│       ├── logger.py            # Advanced logging
│       ├── file_handler.py      # File I/O operations
│       └── validation.py        # Input validation
├── config/                      # Configuration files
│   ├── analysis_config.yaml     # Analysis parameters
│   └── network_config.yaml      # Network configuration
├── scripts/                     # Execution scripts
│   ├── run_analysis.py          # Main analysis script
│   └── batch_analysis.py        # Batch processing
├── tests/                       # Comprehensive test suite
│   ├── test_models.py           # Data model tests
│   ├── test_analyzers.py        # Analyzer tests
│   ├── test_core.py             # Core component tests
│   ├── test_utils.py            # Utility tests
│   └── test_runner.py           # Test execution
├── output/                      # Analysis outputs
│   ├── reports/                 # Generated reports
│   ├── logs/                    # Log files
│   └── data/                    # Raw analysis data
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

### Prerequisites

- PowerFactory 2020 or later
- Python 3.8+
- Windows operating system (PowerFactory requirement)

### Setup

1. **Clone or extract the project:**

   ```bash
   # If using git
   git clone <repository_url>
   cd powerfactory_network_analysis
   ```

2. **Install Python dependencies:**

   ```bash
   # Production dependencies
   pip install -r requirements.txt
   
   # Development dependencies (optional, for testing and development)
   pip install -r requirements-dev.txt
   ```

3. **Verify PowerFactory integration:**

   ```python
   import powerfactory as pf
   app = pf.GetApplication()
   print("PowerFactory integration successful")
   ```

## Usage

### Quick Start

```bash
# Run analysis with default configuration
python scripts/run_analysis.py

# Run with custom configuration
python scripts/run_analysis.py --config my_config.yaml

# Base case analysis only
python scripts/run_analysis.py --base-case-only

# Generate only CSV reports
python scripts/run_analysis.py --format csv
```

### Programmatic Usage

```python
from src.core.network_analyzer import NetworkAnalyzer
from src.core.results_manager import ResultsManager
from src.reports.excel_reporter import ExcelReporter

# Initialize analyzer
analyzer = NetworkAnalyzer()

# Connect to PowerFactory
if analyzer.connect_to_powerfactory():
    # Run full analysis
    results = analyzer.run_full_analysis()
    
    # Process results
    results_manager = ResultsManager()
    results_manager.add_analysis_results(results)
    
    # Generate reports
    excel_reporter = ExcelReporter()
    excel_reporter.generate_report(results_manager, "analysis_report.xlsx")
else:
    print("Failed to connect to PowerFactory")
```

### Batch Analysis

```bash
# Analyze multiple studies
python scripts/batch_analysis.py --studies studies.yaml

# Process multiple configurations
python scripts/batch_analysis.py --configs config1.yaml config2.yaml

# Auto-discover studies in directory
python scripts/batch_analysis.py --study-dir ./studies --pattern "*.pfd"
```

## Configuration

### Analysis Configuration (`config/analysis_config.yaml`)

```yaml
analysis:
  thermal_limits:
    default: 90.0
    lines: 90.0
    transformers: 85.0
    cables: 90.0
  
  voltage_limits:
    scotland:
      33.0: {min: 0.97, max: 1.04}
      11.0: {min: 0.95, max: 1.05}
    england:
      132.0: {min: 0.97, max: 1.04}
      33.0: {min: 0.97, max: 1.04}
      11.0: {min: 0.95, max: 1.05}
  
  options:
    run_base_case: true
    run_contingency: true
    max_contingencies: 1000
    include_out_of_service: false

output:
  formats: [excel, csv]
  excel:
    include_charts: true
    include_summary: true
  sections:
    - violations
    - asset_loading
    - voltage_profiles
    - contingency_summary
```

### Network Configuration (`config/network_config.yaml`)

```yaml
regions:
  scotland:
    name: "Scotland"
    voltage_levels: [33.0, 11.0]
  england:
    name: "England"
    voltage_levels: [132.0, 33.0, 11.0]

element_types:
  thermal_elements:
    - ElmLne    # Lines
    - ElmTr2    # 2-winding transformers
    - ElmTr3    # 3-winding transformers
    - ElmCoup   # Couplers
  voltage_elements:
    - ElmTerm   # Terminals/Busbars
```

## Testing

### Run All Tests

```bash
python tests/test_runner.py
```

### Run Specific Test Modules

```bash
# Test data models
python -m unittest tests.test_models

# Test analyzers
python -m unittest tests.test_analyzers

# Test core components
python -m unittest tests.test_core

# Test utilities
python -m unittest tests.test_utils
```

### Test Coverage

The test suite provides comprehensive coverage of:

- Data model validation and serialization
- Analysis algorithm correctness
- PowerFactory interface operations
- File I/O and configuration validation
- Report generation functionality
- Error handling and edge cases

## Output

### Excel Reports

- **Executive Summary**: High-level analysis overview with charts
- **Violations**: Detailed violation analysis with conditional formatting
- **Thermal Analysis**: Thermal loading results with overload identification
- **Voltage Analysis**: Voltage profile analysis with limit violations
- **Contingency Summary**: Worst contingencies ranked by severity
- **Asset Loading**: Loading distribution and statistics

### CSV Exports

- `violations.csv`: All violations with detailed metadata
- `thermal_analysis.csv`: Thermal analysis results
- `voltage_analysis.csv`: Voltage analysis results
- `contingency_summary.csv`: Contingency ranking and statistics
- `analysis_summary.csv`: Overall analysis summary

### JSON Data

- Complete analysis results in structured JSON format
- Suitable for integration with other tools and systems
- Includes all metadata and contextual information

## Advanced Features

### Violation Severity Assessment

Automated severity classification based on:

- **Thermal**: Percentage over limit (Critical >20%, High >10%, Medium >5%)
- **Voltage**: Deviation from limits (Critical >5%, High >3%, Medium >2%)

### Regional Analysis

Specialized handling for:

- **Scotland**: 33kV and 11kV distribution networks
- **England**: 132kV, 33kV, and 11kV networks
- Region-specific voltage limits and analysis parameters

### Contingency Prioritization

- Intelligent N-1 contingency selection
- Configurable maximum contingency limits
- Results ranked by violation count and severity

### Progress Tracking

- Real-time progress updates during analysis
- Comprehensive logging with multiple output levels
- Performance metrics and timing information

## Troubleshooting

### Common Issues

1. **PowerFactory Connection Failure**

   ```python
   # Ensure PowerFactory is running and accessible
   import powerfactory as pf
   app = pf.GetApplication()
   if app is None:
       print("PowerFactory not found - ensure it's installed and running")
   ```

2. **Configuration Validation Errors**

   ```bash
   # Validate configuration before running
   python scripts/run_analysis.py --validate-config
   ```

3. **Missing Dependencies**

   ```bash
   # Install all required packages
   pip install -r requirements.txt
   ```

4. **File Permission Issues**

   ```bash
   # Ensure output directory is writable
   python scripts/run_analysis.py --output-dir C:/temp/analysis
   ```

### Debug Mode

```bash
# Enable verbose logging
python scripts/run_analysis.py --log-level DEBUG --verbose

# Dry run to test configuration
python scripts/run_analysis.py --dry-run
```

## Performance

### Typical Analysis Times

- **Small Network** (< 100 elements): 1-2 minutes
- **Medium Network** (100-500 elements): 5-10 minutes
- **Large Network** (500+ elements): 15-30 minutes
- **Contingency Analysis**: +50-100% of base case time

### Memory Requirements

- **Minimum**: 4GB RAM
- **Recommended**: 8GB+ RAM for large networks
- **PowerFactory**: Additional memory as per PowerFactory requirements

## Integration

### PowerFactory API Patterns

The project follows PowerFactory best practices:

```python
# Proper object retrieval
objects = app.GetCalcRelevantObjects('*.ElmLne')

# Safe attribute access
value = element.GetAttribute('m:loading')

# Load flow execution
ldf = app.GetFromStudyCase('ComLdf')
error_code = ldf.Execute()
```

### External Tool Integration

- JSON export format for easy integration
- CSV exports compatible with Excel, Power BI, etc.
- Modular design supports custom analysis extensions

## Contributing

### Development Setup

1. Follow installation instructions
2. Run test suite to verify setup
3. Review code structure and patterns
4. Implement new features following existing patterns

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function signatures
- Include comprehensive docstrings
- Add unit tests for new functionality

### Adding New Analyzers

```python
from src.analyzers.base_analyzer import BaseAnalyzer
from src.models.analysis_result import AnalysisType

class CustomAnalyzer(BaseAnalyzer):
    def get_analysis_type(self) -> AnalysisType:
        return AnalysisType.CUSTOM
    
    def analyze_element(self, element, contingency=None):
        # Implement custom analysis logic
        pass
```

## Requirements

- **PowerFactory**: 2020 or later (2021+ recommended)
- **Python**: 3.8+ (3.9+ recommended)
- **Operating System**: Windows (PowerFactory requirement)
- **Memory**: 4GB+ RAM (8GB+ recommended)
- **Storage**: 100MB+ free space for outputs

## Dependencies

See `requirements.txt` for complete list:

- `pyyaml>=6.0`: Configuration file handling
- `pandas>=1.3.0`: Data manipulation and CSV operations
- `openpyxl>=3.0.9`: Excel report generation
- `pathlib`: File system operations (built-in)
- `datetime`: Timestamp handling (built-in)
- `logging`: Advanced logging (built-in)

## License

This project is developed for use with PowerFactory distribution network analysis.

## Author

**Mark Friese**  
Electrical Engineer  
Email: mark.friese.meng@gmail.com  

Specializing in Python automation for Power Systems analysis, with expertise in PowerFactory scripting, distribution network analysis, and power system studies.

### About the Author

Mark is an electrical engineer with a passion for automating power system analysis workflows. He has extensive experience in:

- PowerFactory API development and automation
- Distribution network analysis and modeling
- Python development for engineering applications
- Power system studies and contingency analysis
- Data analysis and visualization for power systems

Connect with Mark:
- Email: mark.friese.meng@gmail.com
- LinkedIn: [Mark Friese](https://linkedin.com/in/mark-friese)
- Medium: [@mark.friese](https://medium.com/@mark.friese)

## Support

For technical support:

1. Check troubleshooting section
2. Review log files for detailed error information
3. Run validation tools to identify configuration issues
4. Consult PowerFactory documentation for API-specific questions
5. Contact the author at mark.friese.meng@gmail.com for specific questions about this implementation
