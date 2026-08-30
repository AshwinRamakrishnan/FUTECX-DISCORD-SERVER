from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import User, Project, ProjectMember
from backend.services.task_service import create_task, submit_task

def test_cross_project():
    db = SessionLocal()
    
    # 1. Create test projects
    proj_a = Project(name="Test Project A", description="A", category="Tech", status="ACTIVE")
    proj_b = Project(name="Test Project B", description="B", category="Tech", status="ACTIVE")
    db.add_all([proj_a, proj_b])
    db.commit()
    db.refresh(proj_a)
    db.refresh(proj_b)
    
    # 2. Create test users
    user_a = User(discord_id="1111", username="member_a")
    user_b = User(discord_id="2222", username="member_b")
    db.add_all([user_a, user_b])
    db.commit()
    db.refresh(user_a)
    db.refresh(user_b)
    
    # 3. Create memberships
    mem_a = ProjectMember(project_id=proj_a.id, user_id=user_a.id, status="APPROVED", role="Member")
    mem_b = ProjectMember(project_id=proj_b.id, user_id=user_b.id, status="APPROVED", role="Member")
    db.add_all([mem_a, mem_b])
    db.commit()
    
    # 4. Create tasks
    task_a = create_task(db, "Task A", "Desc", "Easy", "Tech", 10, proj_a.id)
    task_b = create_task(db, "Task B", "Desc", "Easy", "Tech", 10, proj_b.id)
    
    # 5. Test submissions
    print("Testing MEMBER_A -> PROJECT_A (Expected: Success)")
    try:
        submit_task(db, task_a.id, user_a.id, "http://evidence", "notes")
        print("✅ ALLOWED")
    except Exception as e:
        print(f"❌ DENIED: {e}")
        
    print("Testing MEMBER_A -> PROJECT_B (Expected: Deny)")
    try:
        submit_task(db, task_b.id, user_a.id, "http://evidence", "notes")
        print("❌ ALLOWED (FAIL)")
    except Exception as e:
        print(f"✅ DENIED: {e}")

    print("Testing MEMBER_B -> PROJECT_B (Expected: Success)")
    try:
        submit_task(db, task_b.id, user_b.id, "http://evidence", "notes")
        print("✅ ALLOWED")
    except Exception as e:
        print(f"❌ DENIED: {e}")
        
    print("Testing MEMBER_B -> PROJECT_A (Expected: Deny)")
    try:
        submit_task(db, task_a.id, user_b.id, "http://evidence", "notes")
        print("❌ ALLOWED (FAIL)")
    except Exception as e:
        print(f"✅ DENIED: {e}")
        
    # Cleanup
    db.rollback()
    
if __name__ == "__main__":
    test_cross_project()
