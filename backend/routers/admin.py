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
    from sqlalchemy import func, case

    stats = db.query(
        func.count(User.id).label('total'),
        func.sum(case((User.role == UserRole.ADMIN, 1), else_=0)).label('admins'),
        func.sum(case((User.is_active == True, 1), else_=0)).label('active')
    ).first()
    
    return {
        "total_users": stats.total or 0,
        "admin_count": int(stats.admins) if stats.admins else 0,
        "active_users": int(stats.active) if stats.active else 0,
    }
