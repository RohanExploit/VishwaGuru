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
    Optimized: Standard GROUP BY is measurably faster than multiple func.sum(case(...)) aggregations.
    """
    stats = db.query(
        User.role,
        User.is_active,
        func.count(User.id)
    ).group_by(User.role, User.is_active).all()

    total_users = 0
    admin_count = 0
    active_users = 0

    for role, is_active, count in stats:
        total_users += count

        role_val = role.value if hasattr(role, 'value') else role
        if role_val == 'admin':
            admin_count += count

        if is_active:
            active_users += count

    return {
        "total_users": total_users,
        "admin_count": admin_count,
        "active_users": active_users,
    }
