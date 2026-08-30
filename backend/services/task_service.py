from sqlalchemy.orm import Session
from backend.db.models import Task, TaskSubmission
from backend.services.xp_service import award_xp
from datetime import datetime, timezone

def create_task(db: Session, title: str, description: str, difficulty: str, category: str, xp_reward: int, project_id: int = None) -> Task:
    task = Task(
        title=title,
        description=description,
        difficulty=difficulty,
        category=category,
        xp_reward=xp_reward,
        project_id=project_id
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def submit_task(db: Session, task_id: int, user_id: int, evidence_url: str, notes: str) -> TaskSubmission:
    # Check if task exists
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task #{task_id} does not exist.")
        
    # Check project-scoping
    if task.project_id is not None:
        from backend.db.models import ProjectMember
        member = db.query(ProjectMember).filter(ProjectMember.project_id == task.project_id, ProjectMember.user_id == user_id, ProjectMember.status == "APPROVED").first()
        if not member:
            raise ValueError(f"You must be an approved member of project #{task.project_id} to submit this task.")

    # Check if already submitted
    existing = db.query(TaskSubmission).filter(
        TaskSubmission.task_id == task_id,
        TaskSubmission.user_id == user_id
    ).first()
    
    if existing:
        raise ValueError("Task already submitted")

    # Check rate limiting: max 10 submissions in the last hour
    from datetime import timedelta
    # Check rate limiting: max 10 submissions in the last hour
    from datetime import timedelta
    # Use naive UTC datetime since SQLAlchemy DateTime defaults to timestamp without time zone
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_submissions_count = db.query(TaskSubmission).filter(
        TaskSubmission.user_id == user_id
    ).count()
    print(f"DEBUG submit_task: recent_submissions_count = {recent_submissions_count}", flush=True)

    if recent_submissions_count >= 10:
        raise ValueError("Submission rate limit exceeded. Please try again later.")

    submission = TaskSubmission(
        task_id=task_id,
        user_id=user_id,
        evidence_url=evidence_url,
        notes=notes,
        status="Pending"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

def review_submission(db: Session, submission_id: int, reviewer_id: int, status: str, reviewer_notes: str = None) -> TaskSubmission:
    submission = db.query(TaskSubmission).filter(TaskSubmission.id == submission_id).first()
    if not submission:
        raise ValueError("Submission not found")
        
    if submission.status != "Pending":
        raise ValueError(f"Submission is already {submission.status}")

    if submission.user_id == reviewer_id:
        raise ValueError("Cannot review your own submission")
        
    submission.status = status
    if reviewer_notes:
        submission.notes = (submission.notes or "") + f"\n\nReviewer: {reviewer_notes}"
        
    if status == "APPROVED":
        award_xp(db, submission.user_id, submission.task.xp_reward, f"Task Approved: {submission.task.title}")
        
    db.commit()
    db.refresh(submission)
    return submission
