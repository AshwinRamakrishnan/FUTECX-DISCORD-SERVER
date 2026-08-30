import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base
from backend.db.models import User, Profile, Task, TaskSubmission, XPTransaction, Project, Achievement, Certificate

# Create a clean in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Create tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables after each test
        Base.metadata.drop_all(bind=engine)
