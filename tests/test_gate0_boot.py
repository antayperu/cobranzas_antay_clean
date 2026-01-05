"""
Gate 0 Test: App Initialization
Verifies that app.py can be imported without errors.
This catches missing imports, syntax errors, and circular dependencies.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_app_imports():
    """Test that app.py imports successfully"""
    try:
        # This will fail if there are import errors
        import app
        print("✅ Gate 0 PASS: app.py imports successfully")
        return True
    except Exception as e:
        print(f"❌ Gate 0 FAIL: {e}")
        return False

if __name__ == '__main__':
    success = test_app_imports()
    sys.exit(0 if success else 1)
