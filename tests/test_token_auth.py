"""
Unit tests for token authentication.
"""

import json
import os
import stat
from pathlib import Path

import pytest

from augment_metrics.token_auth import TokenAuth, TokenAuthError


class TestTokenAuth:
    """Tests for TokenAuth class."""
    
    def test_save_and_get_token(self, tmp_path):
        """Test saving and retrieving token."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        auth.save_token("test-token-123", "enterprise-456")
        
        assert auth.get_token() == "test-token-123"
        assert auth.get_enterprise_id() == "enterprise-456"
    
    def test_save_token_creates_file(self, tmp_path):
        """Test that save_token creates credentials file."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        auth.save_token("test-token", "test-id")
        
        assert creds_path.exists()
        assert creds_path.is_file()
    
    def test_save_token_sets_permissions(self, tmp_path):
        """Test that credentials file has user-only permissions."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        auth.save_token("test-token", "test-id")
        
        # Check file permissions (should be 0600)
        file_stat = os.stat(creds_path)
        file_mode = stat.S_IMODE(file_stat.st_mode)
        
        # User should have read and write
        assert file_mode & stat.S_IRUSR
        assert file_mode & stat.S_IWUSR
        
        # Group and others should have no permissions
        assert not (file_mode & stat.S_IRGRP)
        assert not (file_mode & stat.S_IWGRP)
        assert not (file_mode & stat.S_IROTH)
        assert not (file_mode & stat.S_IWOTH)
    
    def test_save_token_empty_raises_error(self, tmp_path):
        """Test that empty token raises error."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        with pytest.raises(TokenAuthError, match="Token cannot be empty"):
            auth.save_token("", "test-id")
        
        with pytest.raises(TokenAuthError, match="Token cannot be empty"):
            auth.save_token("   ", "test-id")
    
    def test_save_enterprise_id_empty_raises_error(self, tmp_path):
        """Test that empty enterprise ID raises error."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        with pytest.raises(TokenAuthError, match="Enterprise ID cannot be empty"):
            auth.save_token("test-token", "")
        
        with pytest.raises(TokenAuthError, match="Enterprise ID cannot be empty"):
            auth.save_token("test-token", "   ")
    
    def test_get_token_no_file(self, tmp_path):
        """Test getting token when file doesn't exist."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        assert auth.get_token() is None
        assert auth.get_enterprise_id() is None
    
    def test_has_credentials(self, tmp_path):
        """Test checking if credentials exist."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        assert not auth.has_credentials()
        
        auth.save_token("test-token", "test-id")
        
        assert auth.has_credentials()
    
    def test_clear_credentials(self, tmp_path):
        """Test clearing credentials."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        auth.save_token("test-token", "test-id")
        assert auth.has_credentials()
        
        auth.clear_credentials()
        
        assert not auth.has_credentials()
        assert not creds_path.exists()
    
    def test_validate_token_format_valid(self, tmp_path):
        """Test validating valid token formats."""
        auth = TokenAuth(credentials_path=tmp_path / "credentials")
        
        assert auth.validate_token_format("valid-token-123")
        assert auth.validate_token_format("a" * 50)
        assert auth.validate_token_format("token-with-dashes-and-numbers-123")
    
    def test_validate_token_format_invalid(self, tmp_path):
        """Test validating invalid token formats."""
        auth = TokenAuth(credentials_path=tmp_path / "credentials")
        
        assert not auth.validate_token_format("")
        assert not auth.validate_token_format("   ")
        assert not auth.validate_token_format("short")
        assert not auth.validate_token_format("token with spaces")
        assert not auth.validate_token_format("token\twith\ttabs")
        assert not auth.validate_token_format("token\nwith\nnewlines")
        assert not auth.validate_token_format(None)
    
    def test_load_credentials_invalid_json(self, tmp_path):
        """Test loading credentials with invalid JSON."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        # Write invalid JSON
        creds_path.write_text("not valid json")
        
        assert auth.get_token() is None
    
    def test_load_credentials_not_dict(self, tmp_path):
        """Test loading credentials that aren't a dictionary."""
        creds_path = tmp_path / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        # Write JSON array instead of object
        creds_path.write_text(json.dumps(["not", "a", "dict"]))
        
        assert auth.get_token() is None
    
    def test_credentials_dir_permissions(self, tmp_path):
        """Test that credentials directory has proper permissions."""
        creds_dir = tmp_path / ".augment"
        creds_path = creds_dir / "credentials"
        auth = TokenAuth(credentials_path=creds_path)
        
        auth.save_token("test-token", "test-id")
        
        # Check directory permissions (should be 0700)
        dir_stat = os.stat(creds_dir)
        dir_mode = stat.S_IMODE(dir_stat.st_mode)
        
        # User should have read, write, and execute
        assert dir_mode & stat.S_IRUSR
        assert dir_mode & stat.S_IWUSR
        assert dir_mode & stat.S_IXUSR
        
        # Group and others should have no permissions
        assert not (dir_mode & stat.S_IRGRP)
        assert not (dir_mode & stat.S_IWGRP)
        assert not (dir_mode & stat.S_IXGRP)
        assert not (dir_mode & stat.S_IROTH)
        assert not (dir_mode & stat.S_IWOTH)
        assert not (dir_mode & stat.S_IXOTH)
