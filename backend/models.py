from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from database import Base
import datetime


class Issue(Base):
    """
    Represents a civic issue reported by a citizen.
    
    Attributes:
        id (int): Unique identifier for the issue (primary key)
        description (str): Detailed description of the issue
        category (str): Category/type of issue (e.g., 'Road', 'Water', 'Garbage', etc.)
                       Indexed for efficient filtering by category
        image_path (str): File path to the uploaded image evidence of the issue
        source (str): Source of the report - either 'telegram' or 'web'
        status (str): Current status of the issue (default: 'open')
                     Indexed for efficient filtering by status
        created_at (datetime): Timestamp when the issue was reported (UTC)
                              Indexed for efficient sorting and filtering
        user_email (str): Email address of the reporter (optional, nullable)
        upvotes (int): Number of upvotes/supporting votes for the issue (default: 0)
                      Indexed for efficient sorting by popularity
    """
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    category = Column(String, index=True)
    image_path = Column(String)
    source = Column(String)  # 'telegram', 'web', etc.
    status = Column(String, default="open", index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    user_email = Column(String, nullable=True)
    upvotes = Column(Integer, default=0, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(String, nullable=True)
    action_plan = Column(Text, nullable=True)
