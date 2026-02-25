from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..core.config import Settings

DATABASE_URL = Settings().DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Returns SQLAlchemy ORM Session with Database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
