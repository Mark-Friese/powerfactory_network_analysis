#!/usr/bin/env python3
"""
Quick test to verify the type errors are fixed.
"""

import sys
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_analyzer_imports():
    """Test analyzer imports specifically."""
    print("Testing analyzer imports...")
    
    try:
        from src.analyzers.thermal_analyzer import ThermalAnalyzer
        print("✓ ThermalAnalyzer imported successfully")
        
        from src.analyzers.voltage_analyzer import VoltageAnalyzer
        print("✓ VoltageAnalyzer imported successfully")
        
        # Test instantiation with mock config
        config = {
            'analysis': {
                'thermal_limits': {
                    'default': 90.0,
                    'lines': 90.0,
                    'transformers': 85.0
                },
                'voltage_limits': {
                    'scotland': {
                        '33.0': {'min': 0.97, 'max': 1.04}
                    }
                }
            }
        }
        
        # Mock PowerFactory interface
        class MockPFInterface:
            def is_connected(self):
                return True
        
        mock_pf = MockPFInterface()
        
        thermal_analyzer = ThermalAnalyzer(mock_pf, config)
        print("✓ ThermalAnalyzer instantiated successfully")
        
        voltage_analyzer = VoltageAnalyzer(mock_pf, config)
        print("✓ VoltageAnalyzer instantiated successfully")
        
        print("\n🎉 All analyzer tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Analyzer test failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_analyzer_imports()
    sys.exit(0 if success else 1)
