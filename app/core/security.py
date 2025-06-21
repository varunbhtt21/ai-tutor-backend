"""
Security utilities for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Union, List
from functools import wraps
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Get password hash"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        if username is None:
            return None
            
        token_data = TokenData(
            username=username, user_id=user_id, role=role
        )
        return token_data
    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        return None


def create_refresh_token(user_id: int) -> str:
    """Create refresh token with longer expiry"""
    data = {"sub": str(user_id), "type": "refresh"}
    expires_delta = timedelta(days=7)  # 7 days for refresh token
    return create_access_token(data, expires_delta)


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode access token - alias for verify_token"""
    return verify_token(token)


# FastAPI security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
            
        # For now, return a mock user object
        # In a real implementation, you would fetch from database
        from app.models.user import User
        user = User(
            id=token_data.user_id or 1,
            username=token_data.username or "test_user",
            email=f"{token_data.username or 'test'}@example.com",
            full_name=token_data.username or "Test User",
            role=token_data.role or "student"
        )
        return user
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise credentials_exception


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """Get current user from JWT token (optional - returns None if no token)"""
    if not credentials:
        return None
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            return None
            
        # Return mock user for testing
        from app.models.user import User
        user = User(
            id=token_data.user_id or 1,
            username=token_data.username or "test_user", 
            email=f"{token_data.username or 'test'}@example.com",
            full_name=token_data.username or "Test User",
            role=token_data.role or "student"
        )
        return user
        
    except Exception as e:
        logger.error(f"Error getting optional user: {e}")
        return None


def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific roles for accessing endpoints
    
    Args:
        allowed_roles: List of roles that are allowed to access the endpoint
    
    Returns:
        Decorated function that checks user role before allowing access
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {allowed_roles}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator 