from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
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
    users = db.query(
        User.id,
        User.email,
        User.full_name,
        User.role,
        User.is_active,
        User.created_at
    ).offset(skip).limit(limit).all()

    # Return list of dictionaries to match UserResponse schema and bypass Pydantic model instantiation overhead
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """
    Get system-wide user statistics.
    Optimized: Uses a single aggregate query to calculate multiple metrics simultaneously,
    reducing database round-trips and scan overhead.
    """
    stats = db.query(
        func.count(User.id).label('total_users'),
        func.sum(case((User.role == UserRole.ADMIN, 1), else_=0)).label('admin_count'),
        func.sum(case((User.is_active == True, 1), else_=0)).label('active_users')
    ).first()

    return {
        "total_users": int(stats.total_users or 0) if stats else 0,
        "admin_count": int(stats.admin_count or 0) if stats else 0,
        "active_users": int(stats.active_users or 0) if stats else 0,
    }
