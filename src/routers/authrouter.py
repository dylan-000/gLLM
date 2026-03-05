from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.schema.models import User
from src.db.database import engine, get_db
from src.models.auth import Token
from src.models.user import UserCreate, UserResponse
from src.services.authservice import login_user, signup_user, get_current_active_user

AuthRouter = APIRouter(prefix="/auth", tags=["auth"])


@AuthRouter.post("/signup")
def signup_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    try:
        signup_user(db=db, user_in=user)
        return Response(status_code=201, content="User Created")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"{str(e)}")
    except Exception as e:
        print(f"POST /signup failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@AuthRouter.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    return login_user(db=db, identifier=form_data.username, password=form_data.password)


@AuthRouter.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    user_out = UserResponse(
        identifier=current_user.identifier,
        id=current_user.id,
        role=current_user.role,
        firstname=current_user.firstname,
        lastname=current_user.lastname,
        email=current_user.email,
        createdAt=current_user.createdAt,
    )
    return user_out