from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from ..schema.models import UserRole


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
