from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import UserResponse
from backend.dependencies import get_current_admin_user

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.get("/users", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.role == UserRole.ADMIN).count()
    
    return {
        "total_users": total_users,
        "admin_count": admin_users,
        "active_users": db.query(User).filter(User.is_active == True).count(),
    }
