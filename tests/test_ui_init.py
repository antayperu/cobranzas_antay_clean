import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent dir to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestUIInitialization(unittest.TestCase):
    
    def setUp(self):
        # Create a new Mock for the module
        self.mock_st = MagicMock()
        # CRITICAL: session_state must be a dict to support ['key'] access
        self.mock_st.session_state = {}
        
        # Configure st.sidebar as a Context Manager
        self.mock_sidebar_context = MagicMock()
        self.mock_st.sidebar.__enter__.return_value = self.mock_sidebar_context
        self.mock_st.sidebar.__exit__.return_value = None
        
        # Configure st.expander as a Context Manager
        self.mock_expander_context = MagicMock()
        self.mock_st.expander.return_value.__enter__.return_value = self.mock_expander_context
        self.mock_st.expander.return_value.__exit__.return_value = None
        
        # Patch sys.modules so imports use our mock
        self.modules_patcher = patch.dict(sys.modules, {'streamlit': self.mock_st})
        self.modules_patcher.start()
        
        # Re-import target modules to ensure they use the patched streamlit
        if 'utils.ui.styles' in sys.modules: del sys.modules['utils.ui.styles']
        if 'utils.ui.sidebar' in sys.modules: del sys.modules['utils.ui.sidebar']
        
        import utils.ui.styles as styles
        import utils.ui.sidebar as ui_sidebar
        self.styles = styles
        self.ui_sidebar = ui_sidebar

    def tearDown(self):
        self.modules_patcher.stop()

    def test_design_system_tokens(self):
        """Verify Design System tokens are present."""
        self.assertIn("primary", self.styles.COLORS)
        self.assertEqual(self.styles.COLORS["primary"], "#0F52BA")
        print("✅ Design System Tokens Verified")

    def test_sidebar_logic_interface_exists(self):
        """Verify Sidebar module structure."""
        self.assertTrue(hasattr(self.ui_sidebar, 'render_sidebar'))
        self.assertTrue(callable(self.ui_sidebar.render_sidebar))
        print("✅ Sidebar Interface Verified")


if __name__ == '__main__':
    unittest.main()
