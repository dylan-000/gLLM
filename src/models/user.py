from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.schema.models import UserRole


class UserCreate(BaseModel):
    """
    User Creation DTO coming from client-side.
    """

    identifier: str
    password: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")


class UserResponse(BaseModel):
    """
    User Response DTO to send to client-side.
    """

    id: UUID
    identifier: str
    role: str
    firstname: Optional[str]
    lastname: Optional[str]
    email: Optional[str]
    createdAt: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    identifier: Optional[str] = None
    password: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
