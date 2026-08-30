from sqlalchemy.orm import Session
from backend.db.models import User, Profile

def get_or_create_user(db: Session, discord_id: str, username: str) -> User:
    user = db.query(User).filter(User.discord_id == discord_id).first()
    if not user:
        user = User(discord_id=discord_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        profile = Profile(user_id=user.id, username=username)
        db.add(profile)
        db.commit()
        db.refresh(user)
    return user

def get_user_by_discord_id(db: Session, discord_id: str) -> User:
    return db.query(User).filter(User.discord_id == discord_id).first()
