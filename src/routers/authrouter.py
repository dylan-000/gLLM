from typing import Annotated
import json

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.schema.models import User
from src.db.database import engine, get_db
from src.models.auth import Token
from src.models.user import UserCreate, UserResponse
from src.services.authservice import (
    login_user,
    signup_user,
    get_current_active_user,
    get_current_active_user_from_cookie,
)
from src.core.config import Settings

AuthRouter = APIRouter(prefix="/auth", tags=["auth"])


@AuthRouter.post("/signup")
def signup_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    Request Body: application/json
    {
      "identifier": str (username),
      "firstname": str,
      "lastname": str,
      "email": str,
      "password": str
    }

    Response: 201 Created
    Note: Does not set auth cookie. User must login after signup.
    """
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
) -> JSONResponse:
    """
    Authenticate user and return JWT token.

    Request Body: application/x-www-form-urlencoded
    username: str
    password: str

    Response: 200 OK
    {
      "access_token": str (JWT),
      "token_type": "bearer"
    }

    Sets HttpOnly cookie 'auth_token' with JWT (30 min TTL)
    """
    token = login_user(
        db=db, identifier=form_data.username, password=form_data.password
    )

    response = JSONResponse(
        content={"access_token": token.access_token, "token_type": token.token_type}
    )

    settings = Settings()
    max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    response.set_cookie(
        key="auth_token",
        value=token.access_token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        path="/",
    )

    return response


@AuthRouter.post("/logout")
async def logout():
    """
    Logout user by clearing auth_token cookie.

    Request Body: empty

    Response: 200 OK
    Clears auth_token cookie on response
    """
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(
        key="auth_token",
        path="/",
    )
    return response


@AuthRouter.get("/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user_from_cookie)],
) -> UserResponse:
    """
    Get current authenticated user information.

    Request: no body (GET request)
    Auth: Reads JWT from auth_token HttpOnly cookie

    Response: 200 OK with UserResponse
    {
      "id": UUID,
      "identifier": str,
      "role": str,
      "firstname": str,
      "lastname": str,
      "email": str,
      "createdAt": datetime
    }

    Returns: 401 Unauthorized if cookie missing or invalid
    """
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
