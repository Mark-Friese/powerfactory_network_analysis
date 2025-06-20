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
from typing import List, Dict, Any


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
    # Possible installation paths
    possible_paths = [
        r"C:\Program Files\DIgSILENT\PowerFactory 2023 SP5",
        r"C:\Program Files (x86)\DIgSILENT\PowerFactory 2023 SP5",
        r"D:\Program Files\DIgSILENT\PowerFactory 2023 SP5",
        # Legacy path from user's request
        r"C:\Program Files\DIgSILENT\PowerFactory 2022 SP3"
    ]
    
    found_installations = []
    
    for path in possible_paths:
        path_obj = Path(path)
        if path_obj.exists():
            # Check for key files
            exe_file = path_obj / "PowerFactory.exe"
            dll_files = {
                "powerfactory.dll": path_obj / "powerfactory.dll",
                "pfapi.dll": path_obj / "pfapi.dll"
            }
            
            installation_info = {
                "path": str(path_obj),
                "exe_exists": exe_file.exists(),
                "dlls": {name: dll_path.exists() for name, dll_path in dll_files.items()},
                "is_target_version": "2023 SP5" in str(path_obj)
            }
            
            found_installations.append(installation_info)
    
    return {
        "found_installations": found_installations,
        "target_version_found": any(inst["is_target_version"] for inst in found_installations),
        "any_version_found": len(found_installations) > 0
    }


def test_powerfactory_import() -> Dict[str, Any]:
    """Test PowerFactory module import."""
    # Configure path before import
    pf_path = r"C:\Program Files\DIgSILENT\PowerFactory 2023 SP5"
    if os.path.exists(pf_path):
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = pf_path + ";" + original_path
    
    try:
        import powerfactory as pf
        import_successful = True
        error_message = None
        
        # Try to get application
        try:
            app = pf.GetApplication()
            app_available = app is not None
            if app:
                # Try to get version info if available
                try:
                    version_info = app.GetVersion()
                except:
                    version_info = "Unknown"
            else:
                version_info = "Application not available"
        except Exception as e:
            app_available = False
            version_info = f"Error getting application: {e}"
            
    except ImportError as e:
        import_successful = False
        app_available = False
        version_info = None
        error_message = str(e)
    except Exception as e:
        import_successful = False
        app_available = False
        version_info = None
        error_message = f"Unexpected error: {e}"
    
    return {
        "import_successful": import_successful,
        "app_available": app_available,
        "version_info": version_info,
        "error_message": error_message
    }


def check_network_analysis_requirements() -> Dict[str, Any]:
    """Check if all network analysis requirements are met."""
    try:
        # Add project src to path
        project_root = Path(__file__).parent.parent
        src_dir = project_root / "src"
        sys.path.insert(0, str(src_dir))
        
        # Test core imports
        from core.powerfactory_interface import PowerFactoryInterface, POWERFACTORY_AVAILABLE, POWERFACTORY_VERSION
        from core.network_analyzer import NetworkAnalyzer
        from models.network_element import NetworkElement, ElementType, Region
        
        imports_successful = True
        error_message = None
        
    except Exception as e:
        imports_successful = False
        error_message = str(e)
        POWERFACTORY_AVAILABLE = False
        POWERFACTORY_VERSION = "Import failed"
    
    return {
        "imports_successful": imports_successful,
        "powerfactory_available": POWERFACTORY_AVAILABLE,
        "powerfactory_version": POWERFACTORY_VERSION,
        "error_message": error_message
    }


def print_results(results: Dict[str, Any]) -> None:
    """Print verification results in a formatted way."""
    print("=" * 70)
    print("PowerFactory 2023 SP5 Setup Verification Results")
    print("=" * 70)
    
    # Python version check
    python_info = results["python"]
    print(f"\n📋 Python Version Check:")
    print(f"   Current Version: {python_info['current_version']}")
    print(f"   Required Version: {python_info['required_version']}")
    print(f"   Compatible: {'✅ Yes' if python_info['compatible'] else '❌ No'}")
    print(f"   Platform: {python_info['platform']}")
    print(f"   Architecture: {python_info['architecture']}")
    
    # PowerFactory installation check
    pf_install = results["installation"]
    print(f"\n🏭 PowerFactory Installation Check:")
    print(f"   Target Version Found: {'✅ Yes' if pf_install['target_version_found'] else '❌ No'}")
    print(f"   Any Version Found: {'✅ Yes' if pf_install['any_version_found'] else '❌ No'}")
    
    if pf_install["found_installations"]:
        print(f"   Found Installations:")
        for i, inst in enumerate(pf_install["found_installations"], 1):
            status = "✅" if inst["is_target_version"] else "⚠️"
            print(f"     {i}. {status} {inst['path']}")
            print(f"        PowerFactory.exe: {'✅' if inst['exe_exists'] else '❌'}")
            for dll_name, dll_exists in inst["dlls"].items():
                print(f"        {dll_name}: {'✅' if dll_exists else '❌'}")
    
    # PowerFactory import test
    pf_import = results["import_test"]
    print(f"\n🐍 PowerFactory Python API Test:")
    print(f"   Import Successful: {'✅ Yes' if pf_import['import_successful'] else '❌ No'}")
    if pf_import['import_successful']:
        print(f"   Application Available: {'✅ Yes' if pf_import['app_available'] else '⚠️ No (PowerFactory not running)'}")
        print(f"   Version Info: {pf_import['version_info']}")
    else:
        print(f"   Error: {pf_import['error_message']}")
    
    # Network analysis requirements
    na_reqs = results["network_analysis"]
    print(f"\n🔌 Network Analysis Requirements:")
    print(f"   Core Imports: {'✅ Yes' if na_reqs['imports_successful'] else '❌ No'}")
    print(f"   PowerFactory Interface: {'✅ Available' if na_reqs['powerfactory_available'] else '❌ Not Available'}")
    print(f"   Detected Version: {na_reqs['powerfactory_version']}")
    if na_reqs['error_message']:
        print(f"   Error: {na_reqs['error_message']}")
    
    # Overall status
    print(f"\n🎯 Overall Status:")
    all_good = (
        python_info['compatible'] and
        pf_install['target_version_found'] and
        pf_import['import_successful'] and
        na_reqs['imports_successful']
    )
    
    if all_good:
        print("   ✅ READY - All requirements met for PowerFactory 2023 SP5")
        print("\n   Next steps:")
        print("   1. Ensure PowerFactory is running")
        print("   2. Open your network model")
        print("   3. Run: python scripts/run_analysis.py --dry-run")
    else:
        print("   ❌ NOT READY - Please address the issues above")
        print("\n   Common solutions:")
        if not python_info['compatible']:
            print("   - Install Python 3.11")
        if not pf_install['target_version_found']:
            print("   - Install PowerFactory 2023 SP5")
        if not pf_import['import_successful']:
            print("   - Configure PowerFactory Python API")
            print("   - Check PowerFactory installation path")


def main() -> int:
    """Main verification function."""
    print("Starting PowerFactory 2023 SP5 setup verification...")
    
    # Run all checks
    results = {
        "python": check_python_version(),
        "installation": check_powerfactory_installation(),
        "import_test": test_powerfactory_import(),
        "network_analysis": check_network_analysis_requirements()
    }
    
    # Print results
    print_results(results)
    
    # Return exit code
    success = (
        results["python"]["compatible"] and
        results["installation"]["target_version_found"] and
        results["import_test"]["import_successful"] and
        results["network_analysis"]["imports_successful"]
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 