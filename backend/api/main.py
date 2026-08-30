from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import User, Profile, Task, TaskSubmission, XPTransaction
from backend.core.config import settings

from fastapi.responses import JSONResponse

app = FastAPI(title="FUTECX API", version="1.0.0")

from backend.api.auth.auth import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

from backend.api.projects import router as projects_router
app.include_router(projects_router, prefix="/api/projects", tags=["projects"])

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Log the full error internally, but return a safe 500 response
    import logging
    logger = logging.getLogger("futecx")
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )

from backend.db.database import SessionLocal, get_db

@app.get("/")
def read_root():
    return {"message": "Welcome to the FUTECX API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for container orchestration (Docker, K8s)."""
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "futecx-api"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})

@app.get("/api/users/{futecx_id}")
def get_user_profile(futecx_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.futecx_id == futecx_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = user.profile
    
    return {
        "futecx_id": user.futecx_id,
        "username": profile.username,
        "level": profile.level,
        "xp": profile.xp,
        "streak": profile.current_streak,
        "joined_at": user.created_at,
        "verification_status": "VERIFIED",
        "official_role": "FUTECX Member",
        "project_count": len(user.projects) if user.projects else 0,
        "qr_verification_url": f"{settings.public_base_url}/api/verify/member/{user.futecx_id}"
    }

@app.get("/api/verify/member/{futecx_id}")
def verify_member(futecx_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.futecx_id == futecx_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Not Found")
        
    return {
        "title": "FUTECX MEMBER VERIFICATION",
        "name": user.profile.username,
        "futecx_id": user.futecx_id,
        "status": "VERIFIED",
        "level": user.profile.level,
        "xp": user.profile.xp,
        "projects_count": len(user.projects) if user.projects else 0,
        "joined_date": user.created_at.strftime('%Y-%m-%d')
    }

@app.get("/api/leaderboard")
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    profiles = db.query(Profile).order_by(Profile.xp.desc()).limit(limit).all()
    
    leaderboard = []
    for rank, p in enumerate(profiles, start=1):
        leaderboard.append({
            "rank": rank,
            "username": p.username,
            "futecx_id": p.user.futecx_id,
            "level": p.level,
            "xp": p.xp
        })
        
    return {"leaderboard": leaderboard}

@app.get("/api/certificates/{cert_id}")
def verify_certificate(cert_id: str, db: Session = Depends(get_db)):
    from backend.db.models import Certificate
    cert = db.query(Certificate).filter(Certificate.cert_id == cert_id).first()
    
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found or invalid")
        
    if cert.is_revoked:
        return {"status": "REVOKED", "message": "This certificate has been revoked."}
        
    return {
        "status": "VALID",
        "cert_id": cert.cert_id,
        "title": cert.title,
        "achievement_text": cert.achievement_text,
        "issued_to": cert.user.profile.username,
        "futecx_id": cert.user.futecx_id,
        "issued_at": cert.issued_at
    }

