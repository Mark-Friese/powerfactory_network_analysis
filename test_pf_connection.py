#!/usr/bin/env python3
"""
Test script to diagnose PowerFactory connection issues with improved interface.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
current_dir = Path(__file__).parent
project_root = current_dir
sys.path.insert(0, str(project_root))

print("=== PowerFactory Connection Diagnostic ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Test 1: Import the PowerFactory interface
print("\n1. Testing PowerFactory interface import...")
try:
    from src.core.powerfactory_interface import PowerFactoryInterface, POWERFACTORY_AVAILABLE, POWERFACTORY_VERSION, POWERFACTORY_PATH
    print("✓ PowerFactory interface imported successfully")
    print(f"✓ PowerFactory available: {POWERFACTORY_AVAILABLE}")
    print(f"✓ PowerFactory version: {POWERFACTORY_VERSION}")
    if POWERFACTORY_PATH:
        print(f"✓ PowerFactory path: {POWERFACTORY_PATH}")
    else:
        print("✗ PowerFactory path not found")
except ImportError as e:
    print(f"✗ PowerFactory interface import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error importing interface: {e}")
    sys.exit(1)

# Test 2: Check PowerFactory installation paths
print("\n2. Checking PowerFactory installation...")
digsilent_path = r"C:\Program Files\DIgSILENT"
if os.path.exists(digsilent_path):
    print(f"✓ DIgSILENT directory found: {digsilent_path}")
    print("Available PowerFactory versions:")
    try:
        for item in os.listdir(digsilent_path):
            item_path = os.path.join(digsilent_path, item)
            if os.path.isdir(item_path) and "PowerFactory" in item:
                print(f"  - {item}")
    except Exception as e:
        print(f"  Error listing directories: {e}")
else:
    print(f"✗ DIgSILENT directory not found: {digsilent_path}")

# Test 3: Initialize PowerFactory interface
print("\n3. Testing PowerFactory interface initialization...")
try:
    pf_interface = PowerFactoryInterface()
    print("✓ PowerFactory interface initialized")
    print(f"✓ PowerFactory available: {pf_interface.is_available}")
except Exception as e:
    print(f"✗ PowerFactory interface initialization failed: {e}")
    sys.exit(1)

# Test 4: Test connection without user ID
if pf_interface.is_available:
    print("\n4. Testing PowerFactory connection (without user)...")
    try:
        success = pf_interface.connect()
        if success:
            print("✓ Successfully connected to PowerFactory without user authentication")
            if pf_interface.is_connected:
                print("✓ Connection verified")
                
                # Try to get some basic info
                try:
                    study_case = pf_interface.get_active_study_case()
                    if study_case:
                        print(f"✓ Active study case found: {study_case}")
                    else:
                        print("? No active study case (this may be normal)")
                except Exception as e:
                    print(f"? Could not get study case info: {e}")
            else:
                print("✗ Connection reported success but is_connected returns False")
        else:
            print("✗ Failed to connect to PowerFactory")
            print("  → PowerFactory may not be running")
            print("  → Please start PowerFactory application and try again")
    except Exception as e:
        print(f"✗ Error connecting to PowerFactory: {e}")
        import traceback
        print("Full error traceback:")
        traceback.print_exc()

    # Test 5: Try with user authentication if provided
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        print(f"\n5. Testing PowerFactory connection with user ID: {user_id}")
        try:
            # Disconnect first
            pf_interface.disconnect()
            
            # Connect with user ID
            success = pf_interface.connect(user_id)
            if success:
                print(f"✓ Successfully connected with user authentication: {user_id}")
                print(f"✓ Current user: {pf_interface.get_current_user()}")
            else:
                print(f"✗ Failed to authenticate user: {user_id}")
                print("  → Check if user ID is correct")
                print("  → Check if user exists in PowerFactory user database")
        except Exception as e:
            print(f"✗ Error with user authentication: {e}")
            import traceback
            print("Full error traceback:")
            traceback.print_exc()
else:
    print("\n4. PowerFactory not available - skipping connection tests")
    print("  → PowerFactory module could not be imported")
    print(f"  → Error: {POWERFACTORY_VERSION}")

print("\n=== Diagnostic Complete ===")
if pf_interface.is_available and not pf_interface.is_connected:
    print("\nTroubleshooting suggestions:")
    print("1. Ensure PowerFactory application is running")
    print("2. Check that you have the correct PowerFactory version installed")
    print("3. Try running PowerFactory as administrator")
    print("4. Check Windows PATH environment variable includes PowerFactory directory") 