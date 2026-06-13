#!/usr/bin/env python3
"""Debug login issue"""

from backend.database import SessionLocal
from backend.models import User
from backend.utils import verify_password

def debug_login():
    db = SessionLocal()
    try:
        email = 'test@example.com'
        password = 'password123'
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f'❌ User not found: {email}')
            return
        
        print(f'✅ User found: {email}')
        print(f'   Full name: {user.full_name}')
        print(f'   Role: {user.role.value}')
        print(f'   Active: {user.is_active}')
        print(f'   Hashed password: {user.hashed_password[:50]}...')
        
        # Test password verification
        is_valid = verify_password(password, user.hashed_password)
        print(f'\n🔐 Password verification: {"✅ VALID" if is_valid else "❌ INVALID"}')
        
        if not is_valid:
            print('\n⚠️  Password does not match!')
            print('   This is why login is failing with 401.')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    debug_login()
