from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import AdminUser
from backend.core.config import settings
from backend.api.auth.schemas import TokenData
from backend.api.auth.auth import ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    admin = db.query(AdminUser).filter(AdminUser.username == token_data.username).first()
    if admin is None:
        raise credentials_exception
    return admin
