"""
Role-Based Access Control (RBAC) system for Rafeeq.
Provides permission checking and role-based access control.
"""

import logging
from typing import Optional, Callable, Awaitable
from functools import wraps
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User, Role
from repositories import UserRepository
from utils.logger import get_logger

logger = get_logger("rafeeq.rbac")


class RBACMiddleware(BaseMiddleware):
    """
    Middleware to inject user role information into handlers.
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable],
        event: TelegramObject,
        data: dict
    ):
        """Inject user role into handler data"""
        db: AsyncSession = data.get("db")
        
        if hasattr(event, 'from_user'):
            user_id = event.from_user.id
            user_repo = UserRepository(db)
            user = await user_repo.get_by_telegram_id(user_id)
            
            if user:
                data["user"] = user
                data["user_role"] = user.role
            else:
                data["user"] = None
                data["user_role"] = Role.USER
        
        return await handler(event, data)


def require_role(*allowed_roles: Role):
    """
    Decorator to restrict handler access to specific roles.
    
    Args:
        *allowed_roles: Allowed roles for this handler
    
    Usage:
        @require_role(Role.ADMIN, Role.SUPER_ADMIN)
        async def admin_handler(message: Message, user_role: Role):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_role from kwargs
            user_role = kwargs.get('user_role')
            
            if user_role not in allowed_roles:
                logger.warning(
                    f"Access denied: User role {user_role} not in allowed roles {allowed_roles}"
                )
                # Return early or raise exception
                return None
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_min_role(min_role: Role):
    """
    Decorator to restrict handler access to users with minimum role level.
    Role hierarchy: USER < PREMIUM < ADMIN < SUPER_ADMIN
    
    Args:
        min_role: Minimum required role
    
    Usage:
        @require_min_role(Role.ADMIN)
        async def admin_handler(message: Message, user_role: Role):
            pass
    """
    role_hierarchy = {
        Role.USER: 0,
        Role.PREMIUM: 1,
        Role.ADMIN: 2,
        Role.SUPER_ADMIN: 3
    }
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_role = kwargs.get('user_role')
            
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(min_role, 0):
                logger.warning(
                    f"Access denied: User role {user_role} below minimum {min_role}"
                )
                return None
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class PermissionChecker:
    """Helper class for checking user permissions"""
    
    @staticmethod
    def has_role(user: User, role: Role) -> bool:
        """Check if user has specific role"""
        return user.role == role
    
    @staticmethod
    def has_any_role(user: User, *roles: Role) -> bool:
        """Check if user has any of the specified roles"""
        return user.role in roles
    
    @staticmethod
    def has_min_role(user: User, min_role: Role) -> bool:
        """Check if user has minimum role level"""
        role_hierarchy = {
            Role.USER: 0,
            Role.PREMIUM: 1,
            Role.ADMIN: 2,
            Role.SUPER_ADMIN: 3
        }
        return role_hierarchy.get(user.role, 0) >= role_hierarchy.get(min_role, 0)
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Check if user is admin or super admin"""
        return user.role in [Role.ADMIN, Role.SUPER_ADMIN]
    
    @staticmethod
    def is_premium(user: User) -> bool:
        """Check if user is premium or higher"""
        return user.role in [Role.PREMIUM, Role.ADMIN, Role.SUPER_ADMIN]
