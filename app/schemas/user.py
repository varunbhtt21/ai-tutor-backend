"""
User-related Pydantic schemas
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.STUDENT


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for user updates"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: UserRole
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse 