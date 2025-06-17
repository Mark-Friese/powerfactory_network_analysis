# VSCode Python Setup Guide for PowerFactory Project

This guide will help you configure VSCode with the correct Python interpreter for PowerFactory development, ensuring compatibility with Python 3.11.9 constraints.

## Quick Setup

1. **Run the Environment Setup Script:**
   ```bash
   python setup_python_env.py
   ```
   This script will verify your Python installation and PowerFactory paths.

2. **Open VSCode in Project Folder:**
   ```bash
   code .
   ```

3. **Install Recommended Extensions:**
   - VSCode will prompt to install recommended extensions from `.vscode/extensions.json`
   - Click "Install All" or install individually

4. **Select Python Interpreter:**
   - Press `Ctrl+Shift+P` 
   - Type "Python: Select Interpreter"
   - Choose Python 3.11.9 (or highest 3.11.x available)

## Detailed Python Interpreter Setup

### Method 1: Using VSCode Command Palette

1. **Open Command Palette:** `Ctrl+Shift+P`
2. **Type:** `Python: Select Interpreter`
3. **Choose from detected interpreters:**
   - Look for Python 3.11.9 or Python 3.11.x
   - Avoid Python 3.12+ (not compatible with PowerFactory)

### Method 2: Manual Path Configuration

If VSCode doesn't detect your Python 3.11.9 installation:

1. **Find your Python 3.11.9 installation:**
   ```bash
   # Check if Python 3.11.9 is in PATH
   python --version
   
   # Find installation paths
   where python
   ```

2. **Common Python 3.11.9 installation paths:**
   - `C:\Python311\python.exe`
   - `C:\Program Files\Python311\python.exe`
   - `C:\Users\[username]\AppData\Local\Programs\Python\Python311\python.exe`

3. **Configure VSCode settings:**
   - Open `.vscode/settings.json` (already configured)
   - Verify the `python.defaultInterpreterPath` points to your Python 3.11.9

### Method 3: Using Virtual Environment

Create a virtual environment with Python 3.11.9:

```bash
# Ensure you're using Python 3.11.9
python3.11 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Then select the virtual environment interpreter in VSCode:
- Path: `./venv/Scripts/python.exe`

## PowerFactory-Specific Configuration

### 1. Verify PowerFactory Paths

The VSCode configuration includes PowerFactory Python paths:

```json
"python.analysis.extraPaths": [
    "${workspaceFolder}/src",
    "C:\\Program Files\\DIgSILENT\\PowerFactory 2021 SP3\\Python\\3.9",
    "C:\\Program Files\\DIgSILENT\\PowerFactory 2022\\Python\\3.9",
    "C:\\Program Files\\DIgSILENT\\PowerFactory 2023\\Python\\3.9"
]
```

### 2. Test PowerFactory Import

Open VSCode terminal and test:

```python
import sys
print(f"Python version: {sys.version}")

# Test PowerFactory import
try:
    import powerfactory as pf
    print("✅ PowerFactory import successful")
except ImportError as e:
    print(f"❌ PowerFactory import failed: {e}")
```

### 3. Environment Variables

The project uses `.env` file for configuration:

```bash
# Copy template and customize
cp .env.template .env

# Edit .env file with your specific paths
POWERFACTORY_PYTHON_PATH=C:\Program Files\DIgSILENT\PowerFactory 2021 SP3\Python\3.9
```

## Troubleshooting Python Interpreter Issues

### Issue 1: VSCode Not Detecting Python 3.11.9

**Solution:**
1. Install Python 3.11.9 from [python.org](https://www.python.org/downloads/release/python-3119/)
2. During installation, check "Add Python to PATH"
3. Restart VSCode
4. Run `Reload Window` command in VSCode

### Issue 2: Multiple Python Versions Causing Confusion

**Solution:**
1. Use explicit Python version:
   ```bash
   # Use specific version
   py -3.11 --version
   
   # Create virtual environment with specific version
   py -3.11 -m venv venv
   ```

2. Update VSCode settings to use specific interpreter:
   ```json
   "python.defaultInterpreterPath": "py -3.11"
   ```

### Issue 3: PowerFactory Module Not Found

**Solution:**
1. Check PowerFactory installation path
2. Add PowerFactory Python path to environment:
   ```bash
   set PYTHONPATH=C:\Program Files\DIgSILENT\PowerFactory 2021 SP3\Python\3.9;%PYTHONPATH%
   ```

3. Or modify Python script to add path:
   ```python
   import sys
   sys.path.insert(0, r"C:\Program Files\DIgSILENT\PowerFactory 2021 SP3\Python\3.9")
   import powerfactory as pf
   ```

### Issue 4: VSCode Terminal Using Wrong Python

**Solution:**
1. Set default terminal profile in `.vscode/settings.json`:
   ```json
   "terminal.integrated.defaultProfile.windows": "PowerFactory Python"
   ```

2. Or manually select terminal profile:
   - Click terminal dropdown arrow
   - Select "PowerFactory Python"

## Verification Steps

### 1. Run Environment Check

```bash
# Use VSCode task (Ctrl+Shift+P -> Tasks: Run Task)
"Setup: Check Python Version"

# Or run manually
python setup_python_env.py
```

### 2. Run Configuration Validation

```bash
# Use VSCode task
"PowerFactory: Validate Configuration"

# Or run manually
python scripts/run_analysis.py --validate-config
```

### 3. Test Analysis (Dry Run)

```bash
# Use VSCode task
"PowerFactory: Dry Run"

# Or run manually
python scripts/run_analysis.py --dry-run --verbose
```

## VSCode Tasks for PowerFactory

The project includes pre-configured tasks (accessible via `Ctrl+Shift+P` -> `Tasks: Run Task`):

### Setup Tasks:
- `Setup: Check Python Version`
- `Setup: Create Virtual Environment`
- `Setup: Verify PowerFactory Paths`
- `PowerFactory: Install Dependencies`

### Analysis Tasks:
- `PowerFactory: Run Full Analysis`
- `PowerFactory: Base Case Only`
- `PowerFactory: Validate Configuration`
- `PowerFactory: Dry Run`

### Testing Tasks:
- `Test: Run All Tests`
- `Test: Coverage Report`

## Debug Configurations

Pre-configured debug setups available in VSCode (`F5` or Run & Debug panel):

- **PowerFactory: Main Analysis** - Debug full analysis with verbose logging
- **PowerFactory: Base Case Only** - Debug base case analysis only
- **PowerFactory: Validate Config Only** - Debug configuration validation
- **Test: Run All Tests** - Debug test suite

## Environment File (.env) Configuration

Key settings for PowerFactory development:

```bash
# Python Configuration
PYTHONPATH=./src
PYTHON_VERSION=3.11.9

# PowerFactory Configuration  
POWERFACTORY_PYTHON_PATH=C:\Program Files\DIgSILENT\PowerFactory 2021 SP3\Python\3.9
POWERFACTORY_DEBUG=false

# Analysis Configuration
DEFAULT_CONFIG_PATH=./config/analysis_config.yaml
LOG_LEVEL=INFO
```

## Best Practices

1. **Always use Python 3.11.x for PowerFactory projects**
2. **Verify PowerFactory module import before analysis**
3. **Use virtual environments for project isolation**
4. **Run validation tasks before actual analysis**
5. **Check logs for any import or path issues**

## Getting Help

If you continue to have Python interpreter issues:

1. **Check the setup script output:** `python setup_python_env.py`
2. **Review VSCode Python documentation:** [VSCode Python](https://code.visualstudio.com/docs/python/python-tutorial)
3. **Contact project author:** mark.friese.meng@gmail.com

## Quick Reference Commands

```bash
# Check Python version
python --version

# Verify PowerFactory import
python -c "import powerfactory; print('Success')"

# Run environment setup
python setup_python_env.py

# Validate project configuration
python scripts/run_analysis.py --validate-config

# Run test analysis
python scripts/run_analysis.py --dry-run
```

---

This configuration ensures optimal compatibility between your Python environment, VSCode, and PowerFactory for professional network analysis development.
