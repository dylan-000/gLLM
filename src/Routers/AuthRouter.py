from fastapi import APIRouter, Depends
from ..Data.database import SessionLocal, engine
from ..Services.AuthService import AuthService
from sqlalchemy.orm import Session
from ..Data.models import User, Base

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

AuthRouter = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(get_db)]
)

auth_service = AuthService()

@AuthRouter.post('/login')

@AuthRouter.post('/signup')

@AuthRouter.get("/users/")
async def read_users(db: Session = Depends(get_db)):
    return auth_service.GetUsers(db=db)
