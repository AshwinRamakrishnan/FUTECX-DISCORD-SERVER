import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db.database import Base
from backend.db.models import User, Profile, Task, TaskSubmission, XPTransaction, AdminUser

def main():
    # 1. Connect to SQLite
    sqlite_url = "sqlite:///./futecx.db.bak"
    sqlite_engine = create_engine(sqlite_url)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_db = SqliteSession()

    # 2. Connect to PostgreSQL
    # Need to get from env or construct
    pg_user = os.environ.get("POSTGRES_USER", "futecx_admin")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "QFMiqMcjLkrToT5mWnoVuf7yBh-oiUq0")
    pg_db = os.environ.get("POSTGRES_DB", "futecx_production")
    # Using localhost for the migration script as it connects from host
    pg_url = f"postgresql://{pg_user}:{pg_pass}@localhost:5432/{pg_db}"
    
    print(f"Connecting to Postgres at {pg_url.replace(pg_pass, '***')}")
    pg_engine = create_engine(pg_url)
    
    # 3. Initialize schema in PostgreSQL
    print("Creating schema in Postgres...")
    Base.metadata.create_all(bind=pg_engine)
    
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    # 4. Migrate Real Data
    print("Migrating Admin Users...")
    for admin in sqlite_db.query(AdminUser).all():
        if admin.id == 1:
            print(f" Migrating AdminUser {admin.username}")
            pg_session.merge(AdminUser(id=admin.id, username=admin.username, hashed_password=admin.hashed_password))

    print("Migrating Users and Profiles...")
    for user in sqlite_db.query(User).all():
        if user.id in [1, 2]:
            print(f" Migrating User {user.futecx_id}")
            new_user = User(
                id=user.id,
                futecx_id=user.futecx_id,
                discord_id=user.discord_id,
                created_at=user.created_at
            )
            pg_session.merge(new_user)
            
            if user.profile:
                print(f"  Migrating Profile for {user.profile.username}")
                new_profile = Profile(
                    id=user.profile.id,
                    user_id=user.profile.user_id,
                    username=user.profile.username,
                    xp=user.profile.xp,
                    level=user.profile.level,
                    current_streak=user.profile.current_streak,
                    interests=user.profile.interests
                )
                pg_session.merge(new_profile)

    print("Migrating Tasks...")
    for task in sqlite_db.query(Task).all():
        if task.id == 1:
            print(f" Migrating Task '{task.title}'")
            new_task = Task(
                id=task.id,
                title=task.title,
                description=task.description,
                difficulty=task.difficulty,
                category=task.category,
                xp_reward=task.xp_reward,
                is_active=task.is_active,
                created_at=task.created_at
            )
            pg_session.merge(new_task)

    print("Migrating Submissions...")
    for sub in sqlite_db.query(TaskSubmission).all():
        if sub.id == 1:
            print(f" Migrating Submission {sub.id}")
            new_sub = TaskSubmission(
                id=sub.id,
                task_id=sub.task_id,
                user_id=sub.user_id,
                evidence_url=sub.evidence_url,
                status=sub.status,
                notes=sub.notes,
                created_at=sub.created_at
            )
            pg_session.merge(new_sub)

    print("Migrating XP Transactions...")
    for tx in sqlite_db.query(XPTransaction).all():
        if tx.id == 1:
            print(f" Migrating XPTransaction {tx.id}")
            new_tx = XPTransaction(
                id=tx.id,
                user_id=tx.user_id,
                amount=tx.amount,
                source=tx.source,
                created_at=tx.created_at
            )
            pg_session.merge(new_tx)

    print("Committing to Postgres...")
    pg_session.commit()
    
    # Fix Sequences for PostgreSQL
    print("Fixing sequences...")
    from sqlalchemy import text
    sequences = [
        ('users_id_seq', 'users'),
        ('profiles_id_seq', 'profiles'),
        ('tasks_id_seq', 'tasks'),
        ('task_submissions_id_seq', 'task_submissions'),
        ('xp_transactions_id_seq', 'xp_transactions'),
        ('admin_users_id_seq', 'admin_users')
    ]
    for seq, table in sequences:
        try:
            pg_session.execute(text(f"SELECT setval('{seq}', (SELECT MAX(id) FROM {table}))"))
            pg_session.commit()
        except Exception as e:
            pg_session.rollback()
            print(f"  Warning: Could not update sequence {seq}: {e}")

    print("Migration Complete.")

if __name__ == "__main__":
    main()
