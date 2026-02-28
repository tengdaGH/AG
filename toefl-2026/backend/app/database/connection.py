from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# For MVP, we'll use SQLite instead of full postgres just to get the schemas wired without a container requirement.
# Wait, the requirements said PostgreSQL. Let's use standard SQLAlchemy with a mock pg connection string.
# In a real environment, this comes from os.getenv("DATABASE_URL")
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../item_bank.db"))
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ──────────────────────────────────────────────────────────────────────────────
# USER PRODUCTION DATABASE (Segregated from Question Bank)
# ──────────────────────────────────────────────────────────────────────────────
user_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../user_data.db"))
SQLALCHEMY_USER_DATABASE_URL = os.getenv("USER_DATABASE_URL", f"sqlite:///{user_db_path}")

user_engine = create_engine(
    SQLALCHEMY_USER_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_USER_DATABASE_URL else {}
)
UserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)

UserBase = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_db():
    db = UserSessionLocal()
    try:
        yield db
    finally:
        db.close()
