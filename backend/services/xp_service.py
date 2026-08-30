from sqlalchemy.orm import Session
from backend.db.models import User, Profile, XPTransaction

LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 250,
    4: 500,
    5: 1000,
    6: 2000,
    7: 4000,
    8: 7500,
    9: 15000,
    10: 30000
}

def calculate_level(xp: int) -> int:
    current_level = 1
    for level, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if xp >= threshold:
            current_level = level
        else:
            break
    return current_level

def award_xp(db: Session, user_id: int, amount: int, source: str) -> dict:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise ValueError("Profile not found")

    # Create transaction
    tx = XPTransaction(user_id=user_id, amount=amount, source=source)
    db.add(tx)
    
    # Update profile XP
    profile.xp += amount
    
    # Check for level up
    new_level = calculate_level(profile.xp)
    leveled_up = False
    if new_level > profile.level:
        profile.level = new_level
        leveled_up = True
        
    db.commit()
    db.refresh(profile)
    
    return {
        "xp_added": amount,
        "new_total": profile.xp,
        "leveled_up": leveled_up,
        "new_level": profile.level
    }
