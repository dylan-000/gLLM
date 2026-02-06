import hashlib
import os
from sqlalchemy.orm import Session
from ..Data import User
from ..Data.database import SessionLocal, engine

class AuthService:
    '''
    Manages Authentication by providing methods to authenticate user login credentials.
    '''

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(AuthService, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        pass
    
    def Authenticate(self, identifier: str, password: str) -> bool:
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

    def GetUsers(self, db: Session) -> list[User] | None:
        return db.query(User).all()