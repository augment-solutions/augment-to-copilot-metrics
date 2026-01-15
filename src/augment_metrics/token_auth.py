"""
Token authentication management for Augment Analytics API.

Handles secure storage and validation of API tokens.
"""

import json
import os
import stat
from pathlib import Path
from typing import Optional


class TokenAuthError(Exception):
    """Base exception for token authentication errors."""
    pass


class TokenAuth:
    """
    Manages API token storage and validation.
    
    Tokens are stored in ~/.augment/credentials with user-only permissions (0600).
    
    Example:
        >>> auth = TokenAuth()
        >>> auth.save_token("my-api-token", "my-enterprise-id")
        >>> token = auth.get_token()
        >>> print(token)
        'my-api-token'
    """
    
    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Initialize TokenAuth.
        
        Args:
            credentials_path: Path to credentials file. Defaults to ~/.augment/credentials
        """
        if credentials_path is None:
            credentials_path = Path.home() / ".augment" / "credentials"
        
        self.credentials_path = credentials_path
        self._ensure_credentials_dir()
    
    def _ensure_credentials_dir(self) -> None:
        """Ensure the credentials directory exists with proper permissions."""
        creds_dir = self.credentials_path.parent
        creds_dir.mkdir(parents=True, exist_ok=True)
        
        # Set directory permissions to user-only (0700)
        os.chmod(creds_dir, stat.S_IRWXU)
    
    def save_token(self, token: str, enterprise_id: str) -> None:
        """
        Save API token and enterprise ID to credentials file.
        
        Args:
            token: Augment API token
            enterprise_id: Augment Enterprise ID
            
        Raises:
            TokenAuthError: If token or enterprise_id is invalid
        """
        # Validate inputs
        if not token or not token.strip():
            raise TokenAuthError("Token cannot be empty")
        
        if not enterprise_id or not enterprise_id.strip():
            raise TokenAuthError("Enterprise ID cannot be empty")
        
        # Prepare credentials data
        credentials = {
            "augment_api_token": token.strip(),
            "enterprise_id": enterprise_id.strip(),
        }
        
        # Write to file
        self.credentials_path.write_text(json.dumps(credentials, indent=2))
        
        # Set file permissions to user-only (0600)
        os.chmod(self.credentials_path, stat.S_IRUSR | stat.S_IWUSR)
    
    def get_token(self) -> Optional[str]:
        """
        Get the stored API token.
        
        Returns:
            The API token if found, None otherwise
        """
        credentials = self._load_credentials()
        return credentials.get("augment_api_token") if credentials else None
    
    def get_enterprise_id(self) -> Optional[str]:
        """
        Get the stored enterprise ID.
        
        Returns:
            The enterprise ID if found, None otherwise
        """
        credentials = self._load_credentials()
        return credentials.get("enterprise_id") if credentials else None
    
    def has_credentials(self) -> bool:
        """
        Check if credentials are stored.
        
        Returns:
            True if credentials file exists and contains valid data
        """
        return self.credentials_path.exists() and self.get_token() is not None
    
    def clear_credentials(self) -> None:
        """Remove stored credentials."""
        if self.credentials_path.exists():
            self.credentials_path.unlink()
    
    def _load_credentials(self) -> Optional[dict]:
        """
        Load credentials from file.
        
        Returns:
            Dictionary with credentials, or None if file doesn't exist or is invalid
        """
        if not self.credentials_path.exists():
            return None
        
        try:
            content = self.credentials_path.read_text()
            credentials = json.loads(content)
            
            # Validate structure
            if not isinstance(credentials, dict):
                return None
            
            return credentials
        except (json.JSONDecodeError, OSError):
            return None
    
    def validate_token_format(self, token: str) -> bool:
        """
        Validate token format (basic checks).
        
        Args:
            token: Token to validate
            
        Returns:
            True if token format appears valid
        """
        if not token or not isinstance(token, str):
            return False
        
        token = token.strip()
        
        # Basic validation: non-empty, reasonable length
        if len(token) < 10:
            return False
        
        # Should not contain whitespace
        if " " in token or "\t" in token or "\n" in token:
            return False
        
        return True

