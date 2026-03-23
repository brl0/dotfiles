"""Access Control and Audit Logging module for pkg-manifest."""

import os
import json
import logging
from pathlib import Path

# Setup Audit Logger path
AUDIT_LOG_FILE = Path(os.path.expanduser("~/.pkgm/audit.log"))

# Standard Roles and Hierarchy
# admin > developer > viewer
ROLE_HIERARCHY = {
    "admin": 3,
    "developer": 2,
    "viewer": 1,
}

# Default role mapping config file
DEFAULT_ROLES_FILE = Path(os.path.expanduser("~/.pkgm/roles.json"))

def _get_logger() -> logging.Logger:
    logger = logging.getLogger("pkgm.audit")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Ensure log directory exists
        try:
            AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(str(AUDIT_LOG_FILE))
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except OSError:
            # Fallback if cannot write to user directory
            pass
    return logger

class AccessManager:
    """Manages role-based access control and audit logging."""
    
    def __init__(self, roles_file: Path = DEFAULT_ROLES_FILE):
        self.roles_file = Path(roles_file)
        self.user_roles = self._load_roles()
        self.current_user = self._get_current_user()

    def _get_current_user(self) -> str:
        """Get the current system username safely."""
        try:
            return os.getlogin()
        except OSError:
            return os.environ.get("USER", "unknown")

    def _load_roles(self) -> dict[str, str]:
        """Load user->role mapping, returns empty dict if no config exists."""
        if self.roles_file.exists():
            try:
                with open(self.roles_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {} 

    def get_user_role(self, username: str) -> str:
        """Get role for username. 
        If no config exists, default to 'admin' (permissive backwards compatibility). 
        If config exists but user not in it, default to 'viewer'."""
        if not self.roles_file.exists():
            return "admin"
        return self.user_roles.get(username, "viewer")

    def check_permission(self, required_role: str, action: str = "") -> bool:
        """Check if current user has the required role (inclusive)."""
        user_role = self.get_user_role(self.current_user)
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        req_level = ROLE_HIERARCHY.get(required_role, 0)
        
        allowed = user_level >= req_level
        
        if not allowed and action:
             _get_logger().warning(f"PERMISSION_DENIED: User '{self.current_user}' attempted '{action}' (requires '{required_role}', has '{user_role}')")
             
        return allowed

    def log_audit(self, action: str, details: str):
         """Log a successful or notable action to the audit log."""
         _get_logger().info(f"AUDIT_ACTION: User '{self.current_user}' performed '{action}': {details}")
