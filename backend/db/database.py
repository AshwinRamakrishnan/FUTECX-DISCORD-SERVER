from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.core.config import settings

engine = create_engine(
    settings.database_url, 
    # check_same_thread=False is needed only for SQLite
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from contextlib import contextmanager

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
