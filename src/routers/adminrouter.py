from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import engine, get_db
from src.models.user import UserResponse, UserUpdate
from src.services.adminservice import AdminService

AdminRouter = APIRouter(prefix="/admin", tags=["admin"])

admin_service = AdminService()


@AdminRouter.get("/users/")
async def read_users(db: Session = Depends(get_db)):
    return admin_service.get_users(db=db)


@AdminRouter.get("/users/{userId}", response_model=UserResponse)
async def get_user_by_id(userId: UUID, db: Session = Depends(get_db)):
    """Get a user by their ID."""
    user = admin_service.get_user_by_id(userId, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@AdminRouter.put("/users/{userId}", response_model=UserResponse)
async def update_user(
    userId: UUID, user_update: UserUpdate, db: Session = Depends(get_db)
):
    """Update a user's fields."""
    # Check if user exists
    user = admin_service.get_user_by_id(userId, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Validate role if provided
    if user_update.role:
        try:
            from src.schema.models import UserRole

            UserRole[user_update.role]
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}",
            )

    try:
        updated_user = admin_service.update_user(
            userId, user_update.model_dump(exclude_unset=True), db
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@AdminRouter.delete("/users/{userId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(userId: UUID, db: Session = Depends(get_db)):
    """Delete a user from the database."""
    user = admin_service.get_user_by_id(userId, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    admin_service.delete_user(userId, db)
    return None
