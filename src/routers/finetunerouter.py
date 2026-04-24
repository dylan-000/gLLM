from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.finetune import (
    FineTuneRequestCreate,
    FineTuneRequestResponse,
    FineTuneRequestUpdate,
    finetune_response_from_orm,
)
from src.schema.models import User, UserRole
from src.services.authservice import get_current_active_user_from_cookie, require_roles_from_cookie
from src.services.finetuneservice import (
    create_finetune_request,
    get_all_finetune_requests,
    update_finetune_request_status,
)

FineTuneRouter = APIRouter(prefix="/finetune", tags=["finetune"])

@FineTuneRouter.post("/requests", response_model=FineTuneRequestResponse)
async def submit_finetune_request(
    req: FineTuneRequestCreate,
    current_user: User = Depends(get_current_active_user_from_cookie),
    db: Session = Depends(get_db)
):
    try:
        new_req = create_finetune_request(db, current_user.id, req)
        # Fetching explicitly to have relationships loaded if needed
        return finetune_response_from_orm(new_req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@FineTuneRouter.get("/requests", response_model=List[FineTuneRequestResponse])
async def get_finetune_requests(
    admin_user: User = Depends(require_roles_from_cookie(UserRole.admin)),
    db: Session = Depends(get_db)
):
    requests = get_all_finetune_requests(db)
    return [finetune_response_from_orm(r) for r in requests]

@FineTuneRouter.put("/requests/{request_id}", response_model=FineTuneRequestResponse)
async def update_finetune_request(
    request_id: UUID,
    update_data: FineTuneRequestUpdate,
    admin_user: User = Depends(require_roles_from_cookie(UserRole.admin)),
    db: Session = Depends(get_db)
):
    try:
        updated_req = update_finetune_request_status(db, request_id, update_data.status)
        return finetune_response_from_orm(updated_req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
