import hashlib
import os

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
    
    def Authenticate(self, username: str, password: str) -> bool:
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
        # This method presumes that the password is stored in the db a specific way
        # it would find the password associated with the username, strip the salt from it
        # then, hash the incoming password and compare it with the one in the db
        
        # soo... how do we get a "user" in the database to begin with....
        