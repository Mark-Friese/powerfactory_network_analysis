#!/usr/bin/env python3
"""
PowerFactory Python Environment Setup and Verification Script

This script helps verify and configure the Python environment for PowerFactory compatibility.
PowerFactory requires Python 3.11.x or lower for optimal compatibility.
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional


def check_python_version() -> Tuple[bool, str]:
    """Check if current Python version is compatible with PowerFactory."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major != 3:
        return False, f"Python {version_str} - PowerFactory requires Python 3.x"
    
    if version.minor > 11:
        return False, f"Python {version_str} - PowerFactory requires Python 3.11.x or lower"
    
    if version.minor < 8:
        return False, f"Python {version_str} - This project requires Python 3.8 or higher"
    
    return True, f"Python {version_str} - Compatible ✓"


def find_powerfactory_paths() -> List[str]:
    """Find PowerFactory installation paths."""
    possible_paths = [
        r"C:\Program Files\DIgSILENT\PowerFactory 2023\Python\3.9",
        r"C:\Program Files\DIgSILENT\PowerFactory 2022\Python\3.9", 
        r"C:\Program Files\DIgSILENT\PowerFactory 2021 SP3\Python\3.9",
        r"C:\Program Files\DIgSILENT\PowerFactory 2021\Python\3.9",
        r"C:\Program Files\DIgSILENT\PowerFactory 2020\Python\3.7",
    ]
    
    found_paths = []
    for path in possible_paths:
        if Path(path).exists():
            found_paths.append(path)
    
    return found_paths


def check_powerfactory_module() -> Tuple[bool, str]:
    """Check if PowerFactory module can be imported."""
    try:
        import powerfactory as pf
        return True, "PowerFactory module imported successfully ✓"
    except ImportError as e:
        return False, f"PowerFactory module import failed: {e}"


def find_python_installations() -> List[Tuple[str, str]]:
    """Find Python installations on the system."""
    installations = []
    
    # Check common Windows installation paths
    common_paths = [
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe", 
        r"C:\Python39\python.exe",
        r"C:\Program Files\Python311\python.exe",
        r"C:\Program Files\Python310\python.exe",
        r"C:\Program Files\Python39\python.exe",
        r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.getenv('USERNAME', '')),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.getenv('USERNAME', '')),
    ]
    
    for path in common_paths:
        if Path(path).exists():
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    installations.append((path, version))
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    
    # Check PATH
    try:
        result = subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            installations.append(("python (PATH)", version))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return installations


def setup_vscode_python_path() -> Optional[str]:
    """Find the best Python installation for VSCode configuration."""
    installations = find_python_installations()
    
    # Prefer Python 3.11.x
    for path, version in installations:
        if "3.11." in version:
            return path.replace("python (PATH)", "python")
    
    # Fallback to any compatible version
    for path, version in installations:
        if any(f"3.{v}." in version for v in [8, 9, 10, 11]):
            return path.replace("python (PATH)", "python")
    
    return None


def generate_vscode_settings(python_path: str) -> dict:
    """Generate VSCode settings.json configuration."""
    powerfactory_paths = find_powerfactory_paths()
    
    settings = {
        "python.defaultInterpreterPath": python_path,
        "python.pythonPath": python_path,
        "python.analysis.extraPaths": [
            "${workspaceFolder}/src",
        ] + powerfactory_paths,
        "python.envFile": "${workspaceFolder}/.env",
    }
    
    return settings


def main():
    """Main setup and verification function."""
    print("=" * 60)
    print("PowerFactory Python Environment Verification")
    print("=" * 60)
    
    # Check current Python version
    is_compatible, version_msg = check_python_version()
    print(f"\n1. Python Version: {version_msg}")
    
    if not is_compatible:
        print("\n⚠️  WARNING: Current Python version may not be compatible with PowerFactory!")
        print("   Recommended: Install Python 3.11.9 for optimal compatibility")
    
    # Check PowerFactory paths
    print("\n2. PowerFactory Installation Paths:")
    pf_paths = find_powerfactory_paths()
    if pf_paths:
        for path in pf_paths:
            print(f"   ✓ {path}")
    else:
        print("   ⚠️  No PowerFactory Python paths found")
        print("   Make sure PowerFactory is installed")
    
    # Check PowerFactory module
    print("\n3. PowerFactory Module:")
    can_import, import_msg = check_powerfactory_module()
    print(f"   {import_msg}")
    
    if not can_import and pf_paths:
        print("\n   Attempting to add PowerFactory path to sys.path...")
        sys.path.insert(0, pf_paths[0])
        can_import, import_msg = check_powerfactory_module()
        print(f"   After path addition: {import_msg}")
    
    # Find Python installations
    print("\n4. Available Python Installations:")
    installations = find_python_installations()
    if installations:
        for path, version in installations:
            compatibility = "✓" if any(f"3.{v}." in version for v in [8, 9, 10, 11]) else "⚠️"
            print(f"   {compatibility} {path} - {version}")
    else:
        print("   ⚠️  No Python installations found")
    
    # VSCode configuration recommendation
    print("\n5. VSCode Configuration Recommendation:")
    recommended_python = setup_vscode_python_path()
    if recommended_python:
        print(f"   Recommended Python interpreter: {recommended_python}")
        print(f"   This is already configured in .vscode/settings.json")
    else:
        print("   ⚠️  No suitable Python installation found for VSCode")
    
    # Environment setup
    print("\n6. Environment Setup:")
    env_template = Path(".env.template")
    env_file = Path(".env")
    
    if env_template.exists() and not env_file.exists():
        print("   Creating .env file from template...")
        env_file.write_text(env_template.read_text())
        print("   ✓ .env file created")
        print("   Please review and modify .env file as needed")
    elif env_file.exists():
        print("   ✓ .env file already exists")
    else:
        print("   ⚠️  .env.template not found")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if is_compatible and can_import:
        print("✅ Environment is ready for PowerFactory development!")
    elif is_compatible and not can_import:
        print("⚠️  Python version is compatible, but PowerFactory module not accessible")
        print("   Make sure PowerFactory is installed and paths are correct")
    elif not is_compatible:
        print("❌ Python version not optimal for PowerFactory")
        print("   Consider installing Python 3.11.9")
    
    print("\nNext steps:")
    print("1. Open VSCode in this project folder")
    print("2. Install recommended extensions from .vscode/extensions.json")
    print("3. Select the correct Python interpreter (Ctrl+Shift+P -> 'Python: Select Interpreter')")
    print("4. Run 'PowerFactory: Validate Configuration' task to test setup")


if __name__ == "__main__":
    main()
