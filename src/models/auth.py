from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.schema.models import UserRole


class Token(BaseModel):
    """
    Represents a JWT Auth token that is returned upon successfull authentication.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
