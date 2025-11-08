"""Secure token storage using OS keychain"""
import keyring
import logging
from config import (
    TOKEN_STORAGE_KEY,
    REFRESH_TOKEN_STORAGE_KEY,
    USER_ID_STORAGE_KEY,
    APP_NAME
)

logger = logging.getLogger(__name__)


class SecureStorage:
    """Handles secure storage of tokens using OS keychain"""
    
    def __init__(self):
        self.service_name = APP_NAME
    
    def save_token(self, token: str) -> bool:
        """Save access token securely"""
        try:
            keyring.set_password(self.service_name, TOKEN_STORAGE_KEY, token)
            return True
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False
    
    def get_token(self) -> str | None:
        """Retrieve access token"""
        try:
            return keyring.get_password(self.service_name, TOKEN_STORAGE_KEY)
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            return None
    
    def save_refresh_token(self, refresh_token: str) -> bool:
        """Save refresh token securely"""
        try:
            keyring.set_password(self.service_name, REFRESH_TOKEN_STORAGE_KEY, refresh_token)
            return True
        except Exception as e:
            logger.error(f"Failed to save refresh token: {e}")
            return False
    
    def get_refresh_token(self) -> str | None:
        """Retrieve refresh token"""
        try:
            return keyring.get_password(self.service_name, REFRESH_TOKEN_STORAGE_KEY)
        except Exception as e:
            logger.error(f"Failed to get refresh token: {e}")
            return None
    
    def save_user_id(self, user_id: str) -> bool:
        """Save user ID"""
        try:
            keyring.set_password(self.service_name, USER_ID_STORAGE_KEY, user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to save user ID: {e}")
            return False
    
    def get_user_id(self) -> str | None:
        """Retrieve user ID"""
        try:
            return keyring.get_password(self.service_name, USER_ID_STORAGE_KEY)
        except Exception as e:
            logger.error(f"Failed to get user ID: {e}")
            return None
    
    def clear_all(self) -> bool:
        """Clear all stored credentials"""
        try:
            keyring.delete_password(self.service_name, TOKEN_STORAGE_KEY)
            keyring.delete_password(self.service_name, REFRESH_TOKEN_STORAGE_KEY)
            keyring.delete_password(self.service_name, USER_ID_STORAGE_KEY)
            return True
        except Exception as e:
            logger.error(f"Failed to clear credentials: {e}")
            return False

