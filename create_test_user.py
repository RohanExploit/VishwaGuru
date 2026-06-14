#!/usr/bin/env python3
"""Create a test user for login testing"""

from backend.database import SessionLocal
from backend.models import User, UserRole
from backend.utils import get_password_hash

def create_test_user():
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == 'test@example.com').first()
        if existing:
            print('❌ User already exists!')
            print('Email: test@example.com')
            return
        
        # Create new user
        user = User(
            email='test@example.com',
            hashed_password=get_password_hash('password123'),
            full_name='Test User',
            role=UserRole.USER,
            is_active=True
        )
        db.add(user)
        db.commit()
        
        print('✅ Test user created successfully!')
        print('Email: test@example.com')
        print('Password: password123')
        print('Role: USER')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_test_user()
