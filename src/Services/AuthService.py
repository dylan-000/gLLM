import hashlib
import os
from sqlalchemy.orm import Session
from ..Data.user import UserCreate
from ..Data.models import User, UserRole
from sqlalchemy import select
import scrypt

class AuthService:
    '''
    Manages Authentication by providing methods to authenticate user login credentials.
    '''
    
    
    def signup_user(self, db: Session, user_in: UserCreate):
        '''
        Creates new user in the database and defaults their role to 'unauthorized'.
        
        :param db: database session
        :type db: Session
        :param user_in: user to signup
        :type user_in: UserCreate
        '''
        existing_user = db.scalar(select(User).where(User.identifier == user_in.identifier).limit(1))
        if existing_user != None:
            raise ValueError("User already exists with this username.")

        user_data = user_in.model_dump(exclude={"password"})
        hashed_password = hash_password(user_in.password)
        db_user = User(**user_data,
                       password=hashed_password,
                       role=UserRole.unauthorized
                       )
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user) # Refreshes DB-generated fields like id and createdAt
            return db_user
        except Exception as e:
            raise Exception(f'Error Adding User to Database: {str(e)}')


    def login_user(self, db: Session, identifier: str, password: str):
        pass

def hash_password(password, maxtime=0.5, datalength=64):
    """Create a secure password hash using scrypt encryption.

    Args:
        password: The password to hash
        maxtime: Maximum time to spend hashing in seconds
        datalength: Length of the random data to encrypt

    Returns:
        bytes: An encrypted hash suitable for storage and later verification
    """
    return scrypt.encrypt(os.urandom(datalength), password, maxtime=maxtime)

def verify_password(hashed_password, guessed_password, maxtime=0.5):
    """Verify a password against its hash with better error handling.

    Args:
        hashed_password: The stored password hash from hash_password()
        guessed_password: The password to verify
        maxtime: Maximum time to spend in verification

    Returns:
        tuple: (is_valid, status_code) where:
            - is_valid: True if password is correct, False otherwise
            - status_code: One of "correct", "wrong_password", "time_limit_exceeded",
            "memory_limit_exceeded", or "error"

    Raises:
        scrypt.error: Only raised for resource limit errors, which you may want to
                    handle by retrying with higher limits or force=True
    """
    try:
        scrypt.decrypt(hashed_password, guessed_password, maxtime, encoding=None)
        return True, "correct"
    except scrypt.error as e:
        # Check the specific error message to differentiate between causes
        error_message = str(e)
        if error_message == "password is incorrect":
            # Wrong password was provided
            return False, "wrong_password"
        elif error_message == "decrypting file would take too long":
            # Time limit exceeded
            raise  # Re-raise so caller can handle appropriately
        elif error_message == "decrypting file would take too much memory":
            # Memory limit exceeded
            raise  # Re-raise so caller can handle appropriately
        else:
            # Some other error occurred (corrupted data, etc.)
            return False, "error"
    