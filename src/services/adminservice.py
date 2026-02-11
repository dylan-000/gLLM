import hashlib
import os
from sqlalchemy.orm import Session
from ..schema.models import User
from sqlalchemy import select


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
