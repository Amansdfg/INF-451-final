"""
Authentication module for Multi-Agent Trading System
"""
from .auth_manager import AuthManager
from .middleware import require_auth, get_current_user

__all__ = ['AuthManager', 'require_auth', 'get_current_user']

