import sys
import os

# Ensure the root 'backend' is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.database.connection import engine, Base
from app.models.models import TestResponse

def main():
    print("Migrating TestResponse to SQLite...")
    Base.metadata.create_all(bind=engine)
    print("Migration successful! TestResponse table created.")

if __name__ == "__main__":
    main()
