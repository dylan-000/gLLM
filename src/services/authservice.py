import hashlib
import jwt
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import Settings
from src.core.core import oauth2_scheme
from src.models.auth import Token, TokenData
from src.models.user import UserCreate
from src.schema.models import User, UserRole
from src.services.adminservice import AdminService
from src.db.database import get_db

SECRET_KEY = Settings().AUTH_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES = Settings().ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = Settings().HASH_ALGORITHM
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")
admin_service = AdminService()


def signup_user(db: Session, user_in: UserCreate):
    """
    Creates new user in the database and defaults their role to 'unauthorized'.

    :param db: database session
    :type db: Session
    :param user_in: user to signup
    :type user_in: UserCreate
    """
    existing_user = db.scalar(
        select(User).where(User.identifier == user_in.identifier).limit(1)
    )
    if existing_user != None:
        raise ValueError("User already exists with this username.")

    user_data = user_in.model_dump(exclude={"password"})
    hashed_password = get_password_hash(user_in.password)
    db_user = User(**user_data, password=hashed_password, role=UserRole.unauthorized)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)  # Refreshes DB-generated fields like id and createdAt
        return db_user
    except Exception as e:
        raise Exception(f"Error Adding User to Database: {str(e)}")


def login_user(db: Session, identifier: str, password: str) -> Token:
    user = authenticate_user(db=db, identifier=identifier, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.identifier}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


def get_password_hash(password):
    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, identifier: str, password: str):
    user = admin_service.get_user_from_identifier(db=db, identifier=identifier)
    if not user:
        verify_password(plain_password=password, hashed_password=DUMMY_HASH)
        return False
    if not verify_password(plain_password=password, hashed_password=user.password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[Session, Depends(get_db)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
        user = admin_service.get_user_from_identifier(
            identifier=token_data.username, db=db
        )
    except InvalidTokenError:
        raise credentials_exception
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error.",
        )
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role == UserRole.unauthorized:
        raise HTTPException(status_code=401, detail="Unauthorized user.")
    return current_user


def require_roles(*allowed_roles: UserRole):
    """
    Factory that returns a dependency enforcing role-based access.
    Usage: Depends(require_roles(UserRole.admin, UserRole.fine_tuner))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker
