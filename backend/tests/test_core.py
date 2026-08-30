from backend.services.user_service import get_or_create_user, get_user_by_discord_id
from backend.services.xp_service import award_xp
from backend.services.task_service import create_task, submit_task, review_submission
from backend.db.models import XPTransaction

def test_user_registration(db_session):
    user = get_or_create_user(db_session, "123456789", "TestUser")
    assert user.discord_id == "123456789"
    assert user.profile.username == "TestUser"
    assert user.futecx_id.startswith("FTX-")
    
    # Check that retrieving the same user doesn't create duplicates
    user2 = get_or_create_user(db_session, "123456789", "TestUser")
    assert user.id == user2.id

def test_xp_and_leveling(db_session):
    user = get_or_create_user(db_session, "987654321", "XPUser")
    
    # Award 50 XP
    result = award_xp(db_session, user.id, 50, "Test Bonus")
    assert result["xp_added"] == 50
    assert result["new_total"] == 50
    assert result["leveled_up"] is False
    assert result["new_level"] == 1
    
    # Verify transaction was created
    tx = db_session.query(XPTransaction).filter(XPTransaction.user_id == user.id).first()
    assert tx is not None
    assert tx.amount == 50
    assert tx.source == "Test Bonus"
    
    # Award more XP to trigger level up to Level 2 (threshold is 100)
    result2 = award_xp(db_session, user.id, 60, "Level Up Bonus")
    assert result2["new_total"] == 110
    assert result2["leveled_up"] is True
    assert result2["new_level"] == 2

def test_task_flow(db_session):
    admin = get_or_create_user(db_session, "admin", "Admin")
    member = get_or_create_user(db_session, "member", "Member")
    
    task = create_task(db_session, "Build API", "Use FastAPI", "Intermediate", "Backend", 100)
    assert task.id is not None
    
    # Member submits
    sub = submit_task(db_session, task.id, member.id, "http://github.com/test", "Done")
    assert sub.status == "Pending"
    
    # Prevent duplicate submission
    import pytest
    with pytest.raises(ValueError, match="Task already submitted"):
        submit_task(db_session, task.id, member.id, "http://github.com/test", "Duplicate")
        
    # Admin rejects
    sub = review_submission(db_session, sub.id, admin.id, "REJECTED", "Needs work")
    assert sub.status == "REJECTED"
    assert member.profile.xp == 0  # No XP awarded for rejection
    
    # We can't re-review a non-pending submission based on current service logic
    with pytest.raises(ValueError, match="Submission is already REJECTED"):
        review_submission(db_session, sub.id, admin.id, "APPROVED", "Good now")

def test_submission_review_regression(db_session):
    admin = get_or_create_user(db_session, "admin2", "Admin2")
    member = get_or_create_user(db_session, "member2", "Member2")
    
    # Create task (this will be linked validly)
    task = create_task(db_session, "API Task", "Description", "Easy", "Backend", 200)
    
    # Member submits
    sub = submit_task(db_session, task.id, member.id, "http://github.com/test", "Done")
    
    # Admin approves
    sub = review_submission(db_session, sub.id, admin.id, "APPROVED", "Great job!")
    assert sub.status == "APPROVED"
    assert member.profile.xp == 200  # XP awarded
    
    # Prevent duplicate review and double XP
    import pytest
    with pytest.raises(ValueError, match="Submission is already APPROVED"):
        review_submission(db_session, sub.id, admin.id, "APPROVED", "Attempt double approve")
    assert member.profile.xp == 200  # XP remains exactly 200

def test_submit_invalid_task(db_session):
    import pytest
    member = get_or_create_user(db_session, "member3", "Member3")
    
    with pytest.raises(ValueError, match="Task #999 does not exist."):
        submit_task(db_session, 999, member.id, "http://evidence", "Notes")

def test_certificate_authorization(db_session):
    from backend.services.certificate_service import issue_certificate, revoke_certificate
    import pytest
    
    member = get_or_create_user(db_session, "cert_member", "CertMember")
    
    # Try to issue certificate without admin rights (should fail)
    with pytest.raises(ValueError, match="Unauthorized: Only authorized staff can issue certificates"):
        issue_certificate(db_session, member.id, "Test Cert", "Completed testing", issuer_is_admin=False)
        
    # Try to issue certificate WITH admin rights (should succeed)
    cert = issue_certificate(db_session, member.id, "Test Cert", "Completed testing", issuer_is_admin=True)
    assert cert.cert_id.startswith("FUTECX-CERT-")
    assert cert.title == "Test Cert"
    
    # Try to revoke without admin rights (should fail)
    with pytest.raises(ValueError, match="Unauthorized: Only authorized staff can revoke certificates"):
        revoke_certificate(db_session, cert.cert_id, issuer_is_admin=False)
        
    # Try to revoke with admin rights (should succeed)
    revoked_cert = revoke_certificate(db_session, cert.cert_id, issuer_is_admin=True)
    assert revoked_cert.is_revoked is True
