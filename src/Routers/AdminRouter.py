from fastapi import APIRouter, Depends
from ..Data.database import get_db, engine
from ..Services.AdminService import AdminService
from sqlalchemy.orm import Session
from ..Data.models import User, Base

AdminRouter = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

admin_service = AdminService()

@AdminRouter.get("/users/")
async def read_users(db: Session = Depends(get_db)):
    return admin_service.get_users(db=db)
