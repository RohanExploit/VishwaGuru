from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any

from backend.priority_engine import priority_engine

router = APIRouter()

class AnalyzeIssueRequest(BaseModel):
    description: str
    image_labels: Optional[List[str]] = None
    category: Optional[str] = None

class AnalyzeIssueResponse(BaseModel):
    severity: str
    severity_score: int
    urgency_score: int
    suggested_categories: List[str]
    reasoning: List[str]

@router.post("/api/analyze-issue", response_model=AnalyzeIssueResponse)
def analyze_issue(request: AnalyzeIssueRequest):
    """
    Analyzes an issue description and optional image labels to determine severity, urgency, and category.
    Fully local execution using the PriorityEngine.
    """
    if not request.description:
        raise HTTPException(status_code=400, detail="Description is required")

    result = priority_engine.analyze(request.description, request.image_labels)

    return AnalyzeIssueResponse(
        severity=result["severity"],
        severity_score=result["severity_score"],
        urgency_score=result["urgency_score"],
        suggested_categories=result["suggested_categories"],
        reasoning=result["reasoning"]
    )
