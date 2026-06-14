from dotenv import load_dotenv
load_dotenv()
from backend.database import SessionLocal
from backend.models import User, UserRole

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == 'admin@vishwaguru.com').first()
    if user:
        user.role = UserRole.ADMIN
        db.commit()
        print('User promoted to ADMIN')
    else:
        print('User not found')
finally:
    db.close()