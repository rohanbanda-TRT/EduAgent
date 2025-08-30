"""Schema for suggested questions."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class QuestionItem(BaseModel):
    """Model for a question item."""
    question: str = Field(..., description="The suggested question text")
    context: str = Field(..., description="Brief context or reason for suggesting this question")
    start_time: str = Field(..., description="Start time of the segment")
    end_time: str = Field(..., description="End time of the segment")
    segment_context: Optional[str] = Field(None, description="Full transcript context for this segment")

class TimeSegment(BaseModel):
    """Model for a time segment with questions."""
    questions: List[QuestionItem] = Field(default=[], description="List of suggested questions for this segment")

class SuggestedQuestions(BaseModel):
    """Schema for suggested questions document."""
    document_id: str = Field(..., description="ID of the document (video)")
    file_id: str = Field(..., description="ID of the file in the files collection")
    organization_id: str = Field(..., description="ID of the organization")
    filename: str = Field(..., description="Original filename")
    display_name: str = Field(..., description="Display name of the file")
    segments: List[TimeSegment] = Field(default=[], description="List of time segments with questions")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

class SuggestedQuestionsResponse(BaseModel):
    """Schema for API response with suggested questions."""
    document_id: str
    file_id: str
    filename: str
    display_name: str
    segments: List[TimeSegment]
