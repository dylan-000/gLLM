from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.finetune import FineTuneRequestCreate
from src.schema.models import FineTuneRequest, FineTuneRequestStatus, User, UserRole


def create_finetune_request(db: Session, user_id: UUID, req: FineTuneRequestCreate) -> FineTuneRequest:
    # Check if user already has a pending request
    existing = db.scalar(
        select(FineTuneRequest).where(
            FineTuneRequest.userId == user_id,
            FineTuneRequest.status == FineTuneRequestStatus.pending
        ).limit(1)
    )
    if existing:
        raise ValueError("You already have a pending fine-tuning request.")

    new_req = FineTuneRequest(
        userId=user_id,
        domain=req.domain,
        description=req.description,
        necessity=req.necessity,
        status=FineTuneRequestStatus.pending
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req


def get_all_finetune_requests(db: Session):
    return db.scalars(
        select(FineTuneRequest).order_by(FineTuneRequest.createdAt.desc())
    ).all()


def update_finetune_request_status(db: Session, request_id: UUID, new_status: str) -> FineTuneRequest:
    req = db.get(FineTuneRequest, request_id)
    if not req:
        raise ValueError("Request not found")

    try:
        status_enum = FineTuneRequestStatus[new_status]
    except KeyError:
        raise ValueError("Invalid status")

    req.status = status_enum
    
    if status_enum == FineTuneRequestStatus.approved:
        user = db.get(User, req.userId)
        if user:
            user.role = UserRole.fine_tuner
            user.finetuner_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            db.add(user)

    db.commit()
    db.refresh(req)
    return req
