from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from ..schema.models import UserRole


class Token(BaseModel):
    """
    Represents a JWT Auth token that is returned upon successfull authentication.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
