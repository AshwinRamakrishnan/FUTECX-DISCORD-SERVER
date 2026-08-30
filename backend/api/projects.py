from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db.models import Project, ProjectMember, User, Task, TaskSubmission, AdminUser
from backend.api.auth.dependencies import get_current_admin

router = APIRouter()

@router.get("/{project_id}")
def get_project_details(project_id: int, db: Session = Depends(get_db)):
    # Public route for dashboard project discovery
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at
    }

@router.get("/{project_id}/tasks")
def get_project_tasks(project_id: int, current_admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    # Protected route, only admin can view all tasks via dashboard for now
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    return {"tasks": [{"id": t.id, "title": t.title, "difficulty": t.difficulty} for t in tasks]}

@router.get("/{project_id}/members")
def get_project_members(project_id: int, current_admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    # Protected route
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "APPROVED").all()
    return {"members": [{"username": m.user.profile.username if m.user.profile else "Unknown", "role": m.role, "joined_at": m.joined_at} for m in members]}

@router.get("/{project_id}/submissions")
def get_project_submissions(project_id: int, current_admin: AdminUser = Depends(get_current_admin), db: Session = Depends(get_db)):
    # Protected route
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    submissions = db.query(TaskSubmission).join(Task).filter(Task.project_id == project_id).all()
        
    return {"submissions": [{"id": s.id, "task_id": s.task_id, "user": s.user.profile.username if s.user.profile else "Unknown", "status": s.status} for s in submissions]}
