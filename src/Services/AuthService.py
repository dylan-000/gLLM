import hashlib
import os
from sqlalchemy.orm import Session
from ..Data import User
from sqlalchemy import select

class AuthService:
    '''
    Manages Authentication by providing methods to authenticate user login credentials.
    '''
    
    def authenticate(self, identifier: str, password: str) -> bool:
        '''
        Parameters
        ----------
        username: str
        password: str

        Returns
        -------
        bool
            True if user is valid. False otherwise.
        '''
    
    def signup_user(self, db: Session, user: User):
        '''
        Creates a new unauthorized user in the database that an admin can then approve.
        '''
        pass

    def get_users(self, db: Session) -> list[User] | None:
        stmt = select(User)
        result = db.execute(stmt)
        return result.scalars().all()
        
    def hash_password(password: str) -> str:
        return ''
    
    '''
    TODO: Alter user entity so that it has a password, email ... etc attributes so that we can authenticate them and create them in the db for admins to approve.
    '''