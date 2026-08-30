from backend.services.user_service import get_or_create_user
from backend.services.task_service import create_task, submit_task, review_submission
from backend.services.certificate_service import issue_certificate, revoke_certificate
from backend.db.models import Certificate, Profile
import pytest

def test_full_member_lifecycle(db_session):
    # 1. Join & Register
    user = get_or_create_user(db_session, "e2e_discord_id", "E2EMember")
    assert user.futecx_id.startswith("FTX-")
    assert user.profile.level == 1
    assert user.profile.xp == 0
    
    # 2. Task creation (Admin)
    task = create_task(db_session, "E2E Task", "Testing E2E", "Expert", "AI", 300)
    
    # 3. Submit Task
    sub = submit_task(db_session, task.id, user.id, "https://github.com/e2e", "E2E proof")
    assert sub.status == "Pending"
    
    # 4. Review Task
    # First test self-approval protection
    with pytest.raises(ValueError, match="Cannot review your own submission"):
        review_submission(db_session, sub.id, user.id, "APPROVED", "I am awesome")
        
    admin = get_or_create_user(db_session, "admin_id", "AdminUser")
    sub = review_submission(db_session, sub.id, admin.id, "APPROVED", "Great job!")
    assert sub.status == "APPROVED"
    
    # 5. Check XP & Level
    db_session.refresh(user)
    assert user.profile.xp == 300
    assert user.profile.level > 1 # 300 XP should easily put them at level 3 (since 250 is level 3)
    
    # 6. Issue Certificate
    from backend.services.certificate_service import issue_certificate
    with pytest.raises(ValueError, match="User not found"):
        issue_certificate(db_session, 9999, "Fake", "Fake", issuer_is_admin=True)
        
    cert = issue_certificate(db_session, user.id, "AI Expert", "Completed E2E Task", issuer_is_admin=True)
    assert cert.cert_id.startswith("FUTECX-CERT-")
    assert cert.is_revoked is False
    
    # 7. Check Verification (Invalid ID)
    from backend.db.models import Certificate
    invalid_cert = db_session.query(Certificate).filter(Certificate.cert_id == "fake-cert").first()
    assert invalid_cert is None
    
    # 8. Check Revocation
    cert = revoke_certificate(db_session, cert.cert_id, issuer_is_admin=True)
    assert cert.is_revoked is True
    
    with pytest.raises(ValueError, match="Certificate not found"):
        revoke_certificate(db_session, "fake-cert", issuer_is_admin=True)
