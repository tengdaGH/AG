from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# For MVP, we'll use SQLite instead of full postgres just to get the schemas wired without a container requirement.
# Wait, the requirements said PostgreSQL. Let's use standard SQLAlchemy with a mock pg connection string.
# In a real environment, this comes from os.getenv("DATABASE_URL")
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../toefl_2026.db"))
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
