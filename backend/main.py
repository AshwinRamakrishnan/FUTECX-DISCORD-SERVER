import asyncio
import threading
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from backend.api.main import app as fastapi_app
from backend.bot.main import run_bot
from backend.db.database import engine, Base
import logging
import sys

# Configure production-safe logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("futecx")

from backend.core.config import settings

def run_api():
    logger.info("Starting FastAPI server on port 8000")
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000, log_level="info")

def main():
    logger.info("Initializing database schema if not exists...")
    try:
        # In production (PostgreSQL), rely on Alembic migrations
        if settings.database_url.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)
            logger.info("Database schema initialized successfully (SQLite mode).")
        else:
            logger.info("Production DB detected. Ensure Alembic migrations are run.")
        
        # Seed initial admin user
        from backend.db.database import SessionLocal
        from backend.db.models import AdminUser
        from passlib.context import CryptContext
        
        db = SessionLocal()
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        admin = db.query(AdminUser).filter(AdminUser.username == settings.admin_username).first()
        if not admin:
            logger.info(f"Seeding initial admin user: {settings.admin_username}")
            hashed_pw = pwd_context.hash(settings.admin_password)
            new_admin = AdminUser(username=settings.admin_username, hashed_password=hashed_pw)
            db.add(new_admin)
            db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # Run API in a separate thread
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Run Discord Bot in the main thread (blocking)
    logger.info("Starting Discord bot...")
    try:
        run_bot()
    except Exception as e:
        logger.error(f"Fatal bot error: {e}")

if __name__ == "__main__":
    main()
