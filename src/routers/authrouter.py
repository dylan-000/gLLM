from fastapi import APIRouter, Depends, HTTPException, Response
from ..db.database import get_db, engine
from ..services.authservice import AuthService
from sqlalchemy.orm import Session
from ..models.user import UserCreate

AuthRouter = APIRouter(prefix="/auth", tags=["auth"])

auth_service = AuthService()


@AuthRouter.post("/signup")
def signup_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        auth_service.signup_user(db=db, user_in=user)
        return Response(status_code=201, content="User Created")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"{str(e)}")
    except Exception as e:
        print(f"POST /signup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
