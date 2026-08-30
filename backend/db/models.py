from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from backend.db.database import Base

def generate_futecx_id():
    # Example generator: FTX-2026-UUID
    return f"FTX-{datetime.now(timezone.utc).year}-{str(uuid.uuid4())[:8].upper()}"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    discord_id = Column(String, unique=True, index=True, nullable=False)
    futecx_id = Column(String, unique=True, index=True, default=generate_futecx_id)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    profile = relationship("Profile", back_populates="user", uselist=False)
    submissions = relationship("TaskSubmission", back_populates="user")
    xp_transactions = relationship("XPTransaction", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    projects = relationship("ProjectMember", back_populates="user")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    username = Column(String, nullable=False)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    current_streak = Column(Integer, default=0)
    interests = Column(String, nullable=True) # comma separated
    
    user = relationship("User", back_populates="profile")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False) # Easy, Intermediate, Advanced, Expert
    category = Column(String, nullable=False)
    xp_reward = Column(Integer, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    submissions = relationship("TaskSubmission", back_populates="task")

class TaskSubmission(Base):
    __tablename__ = "task_submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="Pending") # Pending, Approved, Rejected
    evidence_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="submissions")
    user = relationship("User", back_populates="submissions")

class XPTransaction(Base):
    __tablename__ = "xp_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    source = Column(String, nullable=False) # e.g. "Task Approved", "Onboarding"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="xp_transactions")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=True) # e.g. emoji or image url
    condition = Column(String, nullable=False) # e.g. "reach_level_10", "complete_5_tasks"

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    unlocked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="IDEA") # IDEA, TEAM FORMATION, APPROVED, DEVELOPMENT, TESTING, RELEASED, ARCHIVED
    repo_url = Column(String, nullable=True)
    demo_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    members = relationship("ProjectMember", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="Member") # Owner, Lead, Member, Contributor
    status = Column(String, default="APPROVED") # PENDING, APPROVED, REJECTED, REMOVED
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    removed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="projects")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    location_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    cert_id = Column(String, unique=True, index=True, nullable=False) # e.g. FUTECX-CERT-2026-000124
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    achievement_text = Column(String, nullable=False)
    issued_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_revoked = Column(Boolean, default=False)
    
    user = relationship("User")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ProjectJoinRequest(Base):
    __tablename__ = "project_join_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED, CANCELLED
    requested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    project = relationship("Project")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    action = Column(String, nullable=False) # e.g. "PROJECT_JOIN_APPROVED", "USER_KICKED"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    actor = relationship("User", foreign_keys=[actor_id])
    target = relationship("User", foreign_keys=[target_id])
    project = relationship("Project")

