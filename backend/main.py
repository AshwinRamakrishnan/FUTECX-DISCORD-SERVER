import hashlib
import secrets
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
# PRODUCTION LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("futecx")


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Secure password hashing using PBKDF2-HMAC-SHA256.

    Unlike bcrypt, this does not have bcrypt's 72-byte
    password limitation.
    """

    if not password:
        raise ValueError("Admin password cannot be empty.")

    password_bytes = password.encode("utf-8")

    # Generate random salt
    salt = secrets.token_bytes(16)

    # PBKDF2 iterations
    iterations = 600_000

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt,
        iterations
    )

    return (
        f"pbkdf2_sha256${iterations}$"
        f"{salt.hex()}${derived_key.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify PBKDF2 password hash.
    """

    try:
        algorithm, iterations, salt_hex, hash_hex = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:
        return False


# ============================================================
# FASTAPI SERVER
# ============================================================

def run_api():
    logger.info("Starting FastAPI server on port 8000")

    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    logger.info("Initializing database schema...")

    db = None

    try:

        # ----------------------------------------------------
        # SQLite
        # ----------------------------------------------------

        if settings.database_url.startswith("sqlite"):

            Base.metadata.create_all(bind=engine)

            logger.info(
                "Database schema initialized successfully (SQLite mode)."
            )

        # ----------------------------------------------------
        # PostgreSQL
        # ----------------------------------------------------

        else:

            logger.info(
                "Production PostgreSQL detected."
            )

            # IMPORTANT:
            # Do NOT query tables before they exist.
            #
            # If you are not using Alembic yet, create tables
            # from SQLAlchemy metadata.
            #
            # This prevents:
            # relation "admin_users" does not exist

            Base.metadata.create_all(bind=engine)

            logger.info(
                "Database schema initialized successfully."
            )

        # ----------------------------------------------------
        # IMPORT DB SESSION / MODEL
        # ----------------------------------------------------

        from backend.db.database import SessionLocal
        from backend.db.models import AdminUser

        db = SessionLocal()

        # ----------------------------------------------------
        # CHECK ADMIN USER
        # ----------------------------------------------------

        admin_username = settings.admin_username
        admin_password = settings.admin_password

        if not admin_username:
            raise ValueError(
                "ADMIN_USERNAME environment variable is missing."
            )

        if not admin_password:
            raise ValueError(
                "ADMIN_PASSWORD environment variable is missing."
            )

        admin = (
            db.query(AdminUser)
            .filter(
                AdminUser.username == admin_username
            )
            .first()
        )

        # ----------------------------------------------------
        # CREATE ADMIN
        # ----------------------------------------------------

        if not admin:

            logger.info(
                f"Creating initial admin user: {admin_username}"
            )

            hashed_password = hash_password(
                admin_password
            )

            new_admin = AdminUser(
                username=admin_username,
                hashed_password=hashed_password
            )

            db.add(new_admin)
            db.commit()

            logger.info(
                "Initial admin user created successfully."
            )

        else:

            logger.info(
                f"Admin user '{admin_username}' already exists."
            )

    except Exception as e:

        logger.exception(
            f"Failed to initialize database: {e}"
        )

        raise

    finally:

        if db is not None:
            db.close()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():

    # --------------------------------------------------------
    # Initialize DB
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Start FastAPI
    # --------------------------------------------------------

    api_thread = threading.Thread(
        target=run_api,
        daemon=True
    )

    api_thread.start()

    logger.info(
        "FastAPI server thread started."
    )

    # --------------------------------------------------------
    # Start Discord Bot
    # --------------------------------------------------------

    logger.info(
        "Starting Discord bot..."
    )

    try:

        run_bot()

    except KeyboardInterrupt:

        logger.info(
            "Discord bot stopped."
        )

    except Exception as e:

        logger.exception(
            f"Fatal bot error: {e}"
        )

        raise


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
