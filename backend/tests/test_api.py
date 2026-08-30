from fastapi.testclient import TestClient
from backend.api.main import app
from backend.db.database import get_db
from backend.services.user_service import get_or_create_user
from backend.db.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from backend.db.models import User, Profile, Task, TaskSubmission, XPTransaction, Project, Achievement, Certificate, AdminUser
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_verify_member_valid():
    db = TestingSessionLocal()
    try:
        user = get_or_create_user(db, "verify_user_id", "VerifyUser")
        futecx_id = user.futecx_id
        
        response = client.get(f"/api/verify/member/{futecx_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "FUTECX MEMBER VERIFICATION"
        assert data["futecx_id"] == futecx_id
        assert data["status"] == "VERIFIED"
        assert data["name"] == "VerifyUser"
        assert "xp" in data
        assert "level" in data
        assert "projects_count" in data
        assert "joined_date" in data
        
        # Ensure no secrets
        assert "discord_id" not in data
        assert "password" not in data
    finally:
        db.close()

def test_verify_member_invalid():
    response = client.get("/api/verify/member/FTX-INVALID-ID")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"

def test_auth_login():
    from backend.core.config import settings
    # Ensure the admin user exists for testing
    from backend.db.models import AdminUser
    from passlib.context import CryptContext
    db = TestingSessionLocal()
    try:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        admin = db.query(AdminUser).filter(AdminUser.username == settings.admin_username).first()
        if not admin:
            hashed_pw = pwd_context.hash(settings.admin_password)
            new_admin = AdminUser(username=settings.admin_username, hashed_password=hashed_pw)
            db.add(new_admin)
            db.commit()
    finally:
        db.close()
        
    response = client.post("/api/auth/token", data={
        "username": settings.admin_username,
        "password": settings.admin_password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
def test_auth_invalid_login():
    from backend.core.config import settings
    response = client.post("/api/auth/token", data={
        "username": settings.admin_username,
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    
    response = client.post("/api/auth/token", data={
        "username": "nonexistent",
        "password": "password"
    })
    assert response.status_code == 401

def test_missing_jwt():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_invalid_jwt():
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401

def test_cors_headers():
    from backend.core.config import settings
    response = client.options("/api/verify/member/FTX-123", headers={
        "Origin": settings.frontend_url,
        "Access-Control-Request-Method": "GET"
    })
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_leaderboard():
    db = TestingSessionLocal()
    try:
        u1 = get_or_create_user(db, "u1", "User1")
        u2 = get_or_create_user(db, "u2", "User2")
        u1.profile.xp = 100
        u2.profile.xp = 200
        db.commit()
    finally:
        db.close()
    
    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert "leaderboard" in data
    assert len(data["leaderboard"]) >= 2
    assert data["leaderboard"][0]["xp"] >= data["leaderboard"][1]["xp"] # sorted desc
