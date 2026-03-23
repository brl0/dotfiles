"""Unit tests for the access control module."""

import unittest
from unittest.mock import patch
from pathlib import Path
import json
import tempfile

from access import AccessManager

class TestAccessControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.roles_file = Path(self.temp_dir.name) / "roles.json"
        
    def tearDown(self):
        self.temp_dir.cleanup()
        
    def test_permissive_fallback(self):
        """Test permissive default behavior when config is absent."""
        manager = AccessManager(roles_file=self.roles_file)
        # Should default to 'admin'
        self.assertTrue(manager.check_permission("admin"))
        self.assertTrue(manager.check_permission("developer"))
        
    @patch('os.getlogin', return_value="alice")
    def test_role_enforcement(self, mock_getlogin):
        """Test strict role enforcement when config exists."""
        config = {
            "alice": "developer",
            "bob": "admin",
            "charlie": "viewer"
        }
        with open(self.roles_file, "w") as f:
            json.dump(config, f)
            
        manager = AccessManager(roles_file=self.roles_file)
        
        # developer should have developer and viewer rights, but not admin
        self.assertTrue(manager.check_permission("viewer"))
        self.assertTrue(manager.check_permission("developer"))
        self.assertFalse(manager.check_permission("admin"))
        
    @patch('os.getlogin', return_value="unknown_user")
    def test_unknown_user_role(self, mock_getlogin):
        """Test that unknown users default to the lowest privilege level ('viewer')."""
        config = {
            "alice": "developer"
        }
        with open(self.roles_file, "w") as f:
            json.dump(config, f)
            
        manager = AccessManager(roles_file=self.roles_file)
        self.assertFalse(manager.check_permission("developer"))
        self.assertTrue(manager.check_permission("viewer"))
        
    @patch('os.getlogin', return_value="alice")
    @patch('logging.Logger.warning')
    def test_audit_log_denied(self, mock_warn, mock_getlogin):
        """Test audit logging on permission denied."""
        config = {
            "alice": "viewer"
        }
        with open(self.roles_file, "w") as f:
            json.dump(config, f)
            
        manager = AccessManager(roles_file=self.roles_file)
        result = manager.check_permission("admin", action="delete_db")
        
        self.assertFalse(result)
        mock_warn.assert_called_once()
        self.assertIn("PERMISSION_DENIED: User 'alice' attempted 'delete_db'", mock_warn.call_args[0][0])
        
    @patch('os.getlogin', return_value="bob")
    @patch('logging.Logger.info')
    def test_audit_log_allowed(self, mock_info, mock_getlogin):
        """Test audit log for successful actions."""
        # Assume permissive fallback
        manager = AccessManager(roles_file=self.roles_file)
        manager.log_audit("INSTALL", "test_pkg")
        
        mock_info.assert_called_once()
        self.assertIn("AUDIT_ACTION: User 'bob' performed 'INSTALL': test_pkg", mock_info.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
