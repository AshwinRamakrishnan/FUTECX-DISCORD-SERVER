import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.db.models import Certificate, User

def generate_cert_id():
    return f"FUTECX-CERT-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"

def issue_certificate(db: Session, user_id: int, title: str, achievement_text: str, issuer_is_admin: bool = False) -> Certificate:
    if not issuer_is_admin:
        raise ValueError("Unauthorized: Only authorized staff can issue certificates")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
        
    cert = Certificate(
        cert_id=generate_cert_id(),
        user_id=user.id,
        title=title,
        achievement_text=achievement_text
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert

def revoke_certificate(db: Session, cert_id: str, issuer_is_admin: bool = False) -> Certificate:
    if not issuer_is_admin:
        raise ValueError("Unauthorized: Only authorized staff can revoke certificates")
    cert = db.query(Certificate).filter(Certificate.cert_id == cert_id).first()
    if not cert:
        raise ValueError("Certificate not found")
        
    cert.is_revoked = True
    db.commit()
    db.refresh(cert)
    return cert
