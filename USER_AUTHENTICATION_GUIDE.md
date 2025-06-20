# PowerFactory User Authentication Guide

## Overview

The PowerFactory Network Analysis tool now supports user authentication for PowerFactory connections. This ensures proper access control and logging of who performed each analysis.

## Configuration Methods

### Method 1: Configuration File (Recommended)

Edit `config/analysis_config.yaml` and set your user ID:

```yaml
# PowerFactory connection settings
connection:
  user_id: "your.username"  # Replace with your PowerFactory user ID
  # Leave empty if PowerFactory doesn't require user authentication
```

### Method 2: Command Line Parameter

Use the `--user-id` parameter when running analysis:

```bash
# Run analysis with user authentication
python scripts/run_analysis.py --user-id "your.username"

# Or using short form
python scripts/run_analysis.py -u "your.username"
```

### Method 3: Environment Variable (Optional)

Set your user ID in an environment variable:

```bash
# Windows
set POWERFACTORY_USER=your.username

# Linux/Mac
export POWERFACTORY_USER=your.username
```

## Usage Examples

### Basic Analysis with User Authentication

```bash
# Using config file (recommended)
python scripts/run_analysis.py --dry-run

# Using command line parameter
python scripts/run_analysis.py --user-id "john.doe" --dry-run

# Full analysis with user ID
python scripts/run_analysis.py --user-id "john.doe" --output-dir ./results
```

### Programmatic Usage

```python
from src.core.powerfactory_interface import PowerFactoryInterface

# Initialize interface
pf_interface = PowerFactoryInterface()

# Set user ID
pf_interface.set_user_id("your.username")

# Connect with authentication
success = pf_interface.connect("your.username")

if success:
    print(f"Connected as user: {pf_interface.get_current_user()}")
else:
    print("Authentication failed")
```

## Authentication Process

1. **User ID Configuration**: Set via config file, command line, or programmatically
2. **PowerFactory Connection**: Uses `pf.GetApplicationExt(user_id)` for authenticated connection
3. **Validation**: Confirms successful authentication and application access
4. **Analysis**: Proceeds with authenticated session

**Note**: This follows PowerFactory best practices by using `GetApplicationExt(user_id)` rather than separate login calls.

## Troubleshooting

### Common Issues

1. **Invalid User ID**
   ```
   Error: Login failed for user john.doe with code: 1
   ```
   - **Solution**: Verify your user ID is correct and exists in PowerFactory user database

2. **PowerFactory Not Running**
   ```
   Error: Failed to get PowerFactory application
   ```
   - **Solution**: Start PowerFactory application before running analysis

3. **No User Authentication Required**
   - If your PowerFactory setup doesn't require user authentication, leave `user_id` empty
   - The tool will connect without authentication

### Verification

Test your authentication setup:

```bash
# Test connection with user ID
python verify_powerfactory_setup.py

# Test with specific user ID
python scripts/run_analysis.py --user-id "your.username" --dry-run
```

## Security Notes

- User IDs are logged for audit purposes
- No passwords are stored or transmitted
- PowerFactory handles all authentication validation
- User sessions are properly disconnected after analysis

## Configuration Template

Add this to your `config/analysis_config.yaml`:

```yaml
# PowerFactory connection settings
connection:
  user_id: ""  # Enter your PowerFactory user ID here
  # Examples:
  # user_id: "john.doe"
  # user_id: "j.smith"
  # Leave empty if no authentication required
```

For questions about PowerFactory user management, consult your PowerFactory administrator or the PowerFactory documentation. 