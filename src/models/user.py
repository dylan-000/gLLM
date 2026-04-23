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
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key_set: bool = False

    class Config:
        from_attributes = True


def user_response_from_orm(u: Any) -> UserResponse:
    """Build API user DTO including Langfuse fields (not stored on cl.User in Chainlit)."""
    sk = getattr(u, "langfuse_secret_key", None)
    role = u.role.value if hasattr(u.role, "value") else str(u.role)
    return UserResponse(
        id=u.id,
        identifier=u.identifier,
        role=role,
        firstname=u.firstname,
        lastname=u.lastname,
        email=u.email,
        createdAt=u.createdAt,
        langfuse_public_key=getattr(u, "langfuse_public_key", None),
        langfuse_secret_key_set=bool(sk and str(sk).strip()),
    )


class UserUpdate(BaseModel):
    identifier: Optional[str] = None
    password: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class LangfuseConfigUpdate(BaseModel):
    """
    DTO for updating a user's Langfuse API credentials.
    """
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
