from sqlalchemy import Column, Integer, String, DateTime
from database import Base
import datetime

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    category = Column(String, index=True)
    image_path = Column(String)
    source = Column(String)  # 'telegram', 'web', etc.
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user_email = Column(String, nullable=True)
    upvotes = Column(Integer, default=0)
