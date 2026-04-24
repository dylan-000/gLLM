from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

class FineTuneRequestCreate(BaseModel):
    domain: str
    description: str
    necessity: str

class FineTuneRequestResponse(BaseModel):
    id: UUID
    userId: UUID
    domain: str
    description: str
    necessity: str
    status: str
    createdAt: datetime
    user_identifier: Optional[str] = None

    class Config:
        from_attributes = True

def finetune_response_from_orm(f: Any) -> FineTuneRequestResponse:
    return FineTuneRequestResponse(
        id=f.id,
        userId=f.userId,
        domain=f.domain,
        description=f.description,
        necessity=f.necessity,
        status=f.status.value if hasattr(f.status, "value") else str(f.status),
        createdAt=f.createdAt,
        user_identifier=f.user.identifier if getattr(f, "user", None) else None
    )

class FineTuneRequestUpdate(BaseModel):
    status: str
