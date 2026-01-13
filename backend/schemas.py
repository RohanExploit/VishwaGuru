from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class ActionPlan(BaseModel):
    whatsapp: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    x_post: Optional[str] = None

class ChatRequest(BaseModel):
    query: str

class IssueResponse(BaseModel):
    id: int
    category: str
    description: str
    created_at: datetime
    image_path: Optional[str] = None
    status: str
    upvotes: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    action_plan: Optional[Any] = None

    class Config:
        from_attributes = True

class IssueCreateResponse(BaseModel):
    id: int
    message: str
    action_plan: Optional[ActionPlan] = None

class DetectionResponse(BaseModel):
    detections: List[Any]
