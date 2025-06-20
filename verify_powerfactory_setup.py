#!/usr/bin/env python3
"""
PowerFactory Setup Verification Script

Verifies PowerFactory 2023 SP5 installation and Python 3.11 compatibility.
Run this script before deploying the network analysis application.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any


def check_python_version() -> Dict[str, Any]:
    """Check Python version compatibility."""
    version_info = sys.version_info
    current_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    is_compatible = (
        version_info.major == 3 and 
        version_info.minor == 11
    )
    
    return {
        "current_version": current_version,
        "required_version": "3.11.x",
        "compatible": is_compatible,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0]
    }


def check_powerfactory_installation() -> Dict[str, Any]:
    """Check PowerFactory installation."""
    # Possible installation paths for PowerFactory 2023 SP5
    possible_paths = [
        r"C:\Program Files\DIgSILENT\PowerFactory 2023 SP5",
        r"C:\Program Files (x86)\DIgSILENT\PowerFactory 2023 SP5",
        r"D:\Program Files\DIgSILENT\PowerFactory 2023 SP5",
        # Legacy path (user mentioned 2022 SP3)
        r"C:\Program Files\DIgSILENT\PowerFactory 2022 SP3"
    ]
    
    found_installations = []
    
    for path in possible_paths:
        path_obj = Path(path)
        if path_obj.exists():
            # Check for key files
            exe_file = path_obj / "PowerFactory.exe"
            
            installation_info = {
                "path": str(path_obj),
                "exe_exists": exe_file.exists(),
                "is_target_version": "2023 SP5" in str(path_obj),
                "is_legacy_version": "2022 SP3" in str(path_obj)
            }
            
            found_installations.append(installation_info)
    
    return {
        "found_installations": found_installations,
        "target_version_found": any(inst["is_target_version"] for inst in found_installations),
        "legacy_version_found": any(inst["is_legacy_version"] for inst in found_installations),
        "any_version_found": len(found_installations) > 0
    }


def test_powerfactory_import() -> Dict[str, Any]:
    """Test PowerFactory module import with proper path configuration."""
    # Configure path before import (PowerFactory 2023 SP5)
    pf_path = r"C:\Program Files\DIgSILENT\PowerFactory 2023 SP5"
    
    # Fallback to 2022 SP3 if 2023 SP5 not found
    if not os.path.exists(pf_path):
        pf_path = r"C:\Program Files\DIgSILENT\PowerFactory 2022 SP3"
    
    if os.path.exists(pf_path):
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = pf_path + ";" + original_path
        path_configured = True
    else:
        path_configured = False
    
    try:
        import powerfactory as pf
        import_successful = True
        error_message = None
        
        # Try to get application (this will fail if PowerFactory isn't running)
        try:
            app = pf.GetApplication()
            app_available = app is not None
        except Exception as e:
            app_available = False
            
    except ImportError as e:
        import_successful = False
        app_available = False
        error_message = str(e)
    except Exception as e:
        import_successful = False
        app_available = False
        error_message = f"Unexpected error: {e}"
    
    return {
        "path_configured": path_configured,
        "configured_path": pf_path,
        "import_successful": import_successful,
        "app_available": app_available,
        "error_message": error_message
    }


def main() -> int:
    """Main verification function."""
    print("PowerFactory 2023 SP5 Setup Verification")
    print("=" * 50)
    
    # Check Python version
    python_info = check_python_version()
    print(f"\n1. Python Version Check:")
    print(f"   Current: {python_info['current_version']}")
    print(f"   Required: {python_info['required_version']}")
    print(f"   Status: {'✓ Compatible' if python_info['compatible'] else '✗ Incompatible'}")
    print(f"   Platform: {python_info['platform']}")
    
    # Check PowerFactory installation
    pf_install = check_powerfactory_installation()
    print(f"\n2. PowerFactory Installation Check:")
    
    if pf_install["any_version_found"]:
        for inst in pf_install["found_installations"]:
            version_type = "TARGET" if inst["is_target_version"] else "LEGACY" if inst["is_legacy_version"] else "OTHER"
            status = "✓" if inst["exe_exists"] else "✗"
            print(f"   {status} {version_type}: {inst['path']}")
    else:
        print("   ✗ No PowerFactory installation found")
    
    # Check PowerFactory import
    pf_import = test_powerfactory_import()
    print(f"\n3. PowerFactory Python API Test:")
    print(f"   Path configured: {'✓' if pf_import['path_configured'] else '✗'}")
    print(f"   Using path: {pf_import['configured_path']}")
    print(f"   Import successful: {'✓' if pf_import['import_successful'] else '✗'}")
    
    if not pf_import['import_successful'] and pf_import['error_message']:
        print(f"   Error: {pf_import['error_message']}")
    
    if pf_import['import_successful']:
        print(f"   PowerFactory app: {'✓ Available' if pf_import['app_available'] else '✗ Not running'}")
    
    # Overall assessment
    print(f"\n4. Overall Assessment:")
    
    ready = (
        python_info['compatible'] and
        (pf_install['target_version_found'] or pf_install['legacy_version_found']) and
        pf_import['import_successful']
    )
    
    if ready:
        print("   ✓ READY for network analysis")
        if pf_install['legacy_version_found'] and not pf_install['target_version_found']:
            print("   ⚠ Using legacy PowerFactory version (2022 SP3)")
            print("     Consider upgrading to PowerFactory 2023 SP5")
    else:
        print("   ✗ NOT READY - Issues found:")
        if not python_info['compatible']:
            print("     - Python 3.11 required")
        if not pf_install['any_version_found']:
            print("     - PowerFactory installation not found")
        if not pf_import['import_successful']:
            print("     - PowerFactory Python API not working")
    
    print(f"\nNext steps:")
    if ready:
        print("1. Start PowerFactory application")
        print("2. Open your network model")
        print("3. Run: python test_imports.py")
        print("4. Run: python scripts/run_analysis.py --dry-run")
    else:
        print("1. Install Python 3.11 if needed")
        print("2. Install PowerFactory 2023 SP5")
        print("3. Configure PowerFactory Python API")
        print("4. Re-run this verification script")
    
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main()) 