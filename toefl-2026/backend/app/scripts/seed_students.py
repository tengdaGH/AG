import os
import sys
import uuid

# Add the backend root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.database.connection import SessionLocal
from app.models.models import User, UserRole

def seed_users():
    db = SessionLocal()
    
    allowed_users = ['tengda', 'miya', 'liuyue', 'rita', 'fmingkang', 'haoyu']
    
    print("Seeding student users...")
    print("-" * 40)
    print(f"{'Student ID':<15} | {'Password':<15}")
    print("-" * 40)
    
    for username in allowed_users:
        # Create a simple unique password for this demo
        password = f"{username}2026"
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == username).first()
        
        if existing_user:
            # Update password
            existing_user.password_hash = password
        else:
            # Insert new user
            new_user = User(
                id=str(uuid.uuid4()),
                email=username,
                password_hash=password,
                first_name=username.capitalize(),
                last_name="Student",
                role=UserRole.STUDENT
            )
            db.add(new_user)
            
        print(f"{username:<15} | {password:<15}")
        
    db.commit()
    db.close()
    print("-" * 40)
    print("Done seeding.")

if __name__ == "__main__":
    seed_users()
