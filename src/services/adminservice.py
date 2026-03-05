import hashlib
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.schema.models import User, UserRole
from src.db.database import get_db


class AdminService:
    """
    Service class that provides priveleged admin utilities.
    """

    # TODO: Revise this to use the DTO
    def get_users(self, db: Session) -> list[User]:
        """
        Returns all users.

        :param db: SQLAlchemy Session object
        :type db: Session
        :return: Description
        :rtype: list[User] | None
        """
        stmt = select(User)
        result = db.execute(stmt)
        return result.scalars().all()

    def get_user_from_identifier(self, identifier: str, db: Session) -> User:
        stmt = select(User).where(User.identifier == identifier).limit(1)
        result = db.scalar(stmt)
        return result

    def get_user_by_id(self, user_id: UUID, db: Session) -> User | None:
        """
        Returns a user by their ID.

        :param user_id: UUID of the user
        :type user_id: UUID
        :param db: SQLAlchemy Session object
        :type db: Session
        :return: User object or None if not found
        :rtype: User | None
        """
        stmt = select(User).where(User.id == user_id).limit(1)
        result = db.execute(stmt)
        return result.scalar()

    def update_user(self, user_id: UUID, user_data: dict, db: Session) -> User | None:
        """
        Updates a user's fields.

        :param user_id: UUID of the user to update
        :type user_id: UUID
        :param user_data: Dictionary of fields to update
        :type user_data: dict
        :param db: SQLAlchemy Session object
        :type db: Session
        :return: Updated User object or None if not found
        :rtype: User | None
        """
        user = self.get_user_by_id(user_id, db)
        if not user:
            return None

        # Validate role if provided
        if "role" in user_data and user_data["role"]:
            try:
                UserRole[user_data["role"]]
            except KeyError:
                raise ValueError(f"Invalid role: {user_data['role']}")

        # Update only provided fields
        for key, value in user_data.items():
            if value is not None:
                setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, user_id: UUID, db: Session) -> bool:
        """
        Deletes a user from the database.

        :param user_id: UUID of the user to delete
        :type user_id: UUID
        :param db: SQLAlchemy Session object
        :type db: Session
        :return: True if user was deleted, False if not found
        :rtype: bool
        """
        user = self.get_user_by_id(user_id, db)
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True