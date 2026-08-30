from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db.models import User, Project, ProjectMember, Task, TaskSubmission, XPTransaction
from backend.services.task_service import create_task, submit_task, review_submission
from datetime import datetime, timezone, timedelta
import uuid

def test_task_service():
    db = SessionLocal()
    try:
        # Create user and profile
        user = User(discord_id='testuser_' + str(uuid.uuid4()))
        db.add(user)
        db.commit()
        db.refresh(user)

        from backend.db.models import Profile
        profile = Profile(user_id=user.id, username='testuser')
        db.add(profile)
        db.commit()
        db.refresh(user)

        # Create project and membership for C
        proj = Project(name='Test Proj ' + str(uuid.uuid4()), description='desc', status='ACTIVE')
        db.add(proj)
        db.commit()
        db.refresh(proj)
        
        mem = ProjectMember(project_id=proj.id, user_id=user.id, status='APPROVED', role='Member')
        db.add(mem)
        db.commit()
        
        # Test C: unauthorized project (user not in this one)
        proj_unauth = Project(name='Unauth Proj ' + str(uuid.uuid4()), description='desc', status='ACTIVE')
        db.add(proj_unauth)
        db.commit()
        db.refresh(proj_unauth)
        
        task_unauth = create_task(db, 'Unauth task', 'desc', 'easy', 'cat', 10, proj_unauth.id)
        print('Test C: Unauthorized project')
        try:
            submit_task(db, task_unauth.id, user.id, 'url', 'notes')
            print('❌ FAIL: Allowed unauthorized project task submission')
        except ValueError as e:
            if 'approved member' in str(e):
                print('✅ PASS: Unauthorized project rejected')
            else:
                print(f'❌ FAIL: Wrong error message: {e}')

        # Test A: normal submission
        task1 = create_task(db, 'Task 1', 'desc', 'easy', 'cat', 10, proj.id)
        print('\nTest A: Normal submission')
        try:
            sub1 = submit_task(db, task1.id, user.id, 'url', 'notes')
            print('✅ PASS: Normal submission allowed')
        except Exception as e:
            print(f'❌ FAIL: Normal submission failed: {e}')

        # Test B: duplicate submission
        print('\nTest B: Duplicate submission')
        try:
            submit_task(db, task1.id, user.id, 'url', 'notes')
            print('❌ FAIL: Duplicate submission allowed')
        except ValueError as e:
            if 'already submitted' in str(e):
                print('✅ PASS: Duplicate submission rejected')
            else:
                print(f'❌ FAIL: Wrong error message: {e}')

        # Test D: Rate limit exceeded (10 submissions in an hour)
        print('\nTest D: Rate limit exceeded')
        # User already has 1 submission. Add 9 more successfully.
        tasks = [create_task(db, f'Task limit {i}', 'desc', 'easy', 'cat', 10, proj.id) for i in range(2, 11)]
        for t in tasks:
            submit_task(db, t.id, user.id, 'url', 'notes')
        
        # Now the 11th should fail
        task_11 = create_task(db, 'Task 11', 'desc', 'easy', 'cat', 10, proj.id)
        try:
            submit_task(db, task_11.id, user.id, 'url', 'notes')
            print('❌ FAIL: 11th submission allowed (Rate limit bypassed)')
        except ValueError as e:
            if 'rate limit exceeded' in str(e):
                print('✅ PASS: Rate limit enforced')
            else:
                print(f'❌ FAIL: Wrong error message: {e}')

        # Test E: Approved submission -> XP flow unchanged
        print('\nTest E: Approved submission XP flow')
        admin = User(discord_id='admin_' + str(uuid.uuid4()))
        db.add(admin)
        db.commit()
        db.refresh(admin)

        try:
            initial_xp = user.profile.xp if user.profile else 0
            review_submission(db, sub1.id, admin.id, 'APPROVED', 'Good job')
            db.refresh(user)
            final_xp = user.profile.xp if user.profile else 0
            if final_xp > initial_xp:
                print('✅ PASS: XP awarded correctly')
            else:
                print('❌ FAIL: XP not awarded')
        except Exception as e:
            print(f'❌ FAIL: XP approval flow broke: {e}')

    finally:
        db.rollback()

if __name__ == '__main__':
    test_task_service()
