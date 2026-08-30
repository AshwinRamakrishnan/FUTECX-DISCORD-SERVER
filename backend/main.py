import asyncio
import os
import threading
import uvicorn
import logging
import sys

from fastapi.middleware.cors import CORSMiddleware

from backend.api.main import app as fastapi_app
from backend.bot.main import run_bot
from backend.db.database import engine, Base
from backend.core.config import settings


# ============================================================
# PRODUCTION-SAFE LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("futecx")


# ============================================================
# FASTAPI SERVER
# ============================================================

def run_api():
    """
    Start FastAPI using Render's PORT environment variable.
    Falls back to 8000 for local development.
    """

    port = int(os.getenv("PORT", "8000"))

    logger.info(
        f"Starting FastAPI server on 0.0.0.0:{port}"
    )

    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


# ============================================================
# DATABASE INITIALIZATION + ADMIN SEEDING
# ============================================================

def initialize_database():
    """
    Initialize database tables and create the initial admin user.
    Works with both SQLite and PostgreSQL.
    """

    logger.info("Initializing database schema...")

    try:
        # ----------------------------------------------------
        # Create all SQLAlchemy tables
        # ----------------------------------------------------

        Base.metadata.create_all(bind=engine)

        logger.info(
            "Database schema initialized successfully."
        )

        # ----------------------------------------------------
        # Seed initial admin user
        # ----------------------------------------------------

        from backend.db.database import SessionLocal
        from backend.db.models import AdminUser
        from passlib.context import CryptContext

        db = SessionLocal()

        try:
            pwd_context = CryptContext(
                schemes=["bcrypt"],
                deprecated="auto"
            )

            admin = (
                db.query(AdminUser)
                .filter(
                    AdminUser.username
                    == settings.admin_username
                )
                .first()
            )

            if not admin:
                logger.info(
                    f"Creating initial admin user: "
                    f"{settings.admin_username}"
                )

                hashed_pw = pwd_context.hash(
                    settings.admin_password
                )

                new_admin = AdminUser(
                    username=settings.admin_username,
                    hashed_password=hashed_pw
                )

                db.add(new_admin)
                db.commit()

                logger.info(
                    "Initial admin user created successfully."
                )

            else:
                logger.info(
                    "Admin user already exists. "
                    "Skipping admin seeding."
                )

        finally:
            db.close()

    except Exception as e:
        logger.exception(
            f"Failed to initialize database: {e}"
        )
        raise


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # --------------------------------------------------------
    # Initialize PostgreSQL / SQLite database
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Start FastAPI in background thread
    # --------------------------------------------------------

    api_thread = threading.Thread(
        target=run_api,
        daemon=True
    )

    api_thread.start()

    logger.info(
        "FastAPI server started in background thread."
    )

    # --------------------------------------------------------
    # Start Discord Bot
    # --------------------------------------------------------

    logger.info(
        "Starting Discord bot..."
    )

    try:
        run_bot()

    except Exception as e:
        logger.exception(
            f"Fatal Discord bot error: {e}"
        )
        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
