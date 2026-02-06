from fastapi import APIRouter, Depends
from ..Data.database import get_db, engine
from ..Services.AuthService import AuthService
from sqlalchemy.orm import Session
from ..Data.models import User, Base

AuthRouter = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

auth_service = AuthService()

#@AuthRouter.post('/login')
#@AuthRouter.post('/signup')

@AuthRouter.get("/users/")
async def read_users(db: Session = Depends(get_db)):
    return auth_service.get_users(db=db)
