"""
Data models for call logs and webhook integration
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class SpeakerType(str, Enum):
    AGENT = "agent"
    USER = "user"

class CallOutcome(str, Enum):
    RESOLVED = "resolved"
    TRANSFER_TO_HUMAN = "transfer_to_human"
    NO_ANSWER = "no_answer"
    ESCALATED = "escalated"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class TranscriptEntry(BaseModel):
    """Individual transcript entry"""
    speaker: SpeakerType
    text: str
    timestamp: float = Field(..., description="Timestamp in seconds from call start")

class InteractionLog(BaseModel):
    """Complete interaction log from ElevenLabs webhook"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    agent_id: str = Field(..., description="ElevenLabs agent ID")
    timestamp: datetime = Field(..., description="Call start timestamp")
    duration_seconds: int = Field(..., description="Total call duration in seconds")
    transcript: List[TranscriptEntry] = Field(..., description="Full conversation transcript")
    summary: str = Field(..., description="AI-generated conversation summary")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Structured data extracted from conversation")
    sentiment: Optional[SentimentType] = Field(None, description="Overall conversation sentiment")
    call_outcome: Optional[CallOutcome] = Field(None, description="How the call ended")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StudentStatusRequest(BaseModel):
    """Request for student application status"""
    student_name: str = Field(..., description="Student's full name")
    student_email: str = Field(..., description="Student's email address")

class StudentStatusResponse(BaseModel):
    """Response for student application status"""
    found: bool = Field(..., description="Whether student was found in system")
    status: Optional[str] = Field(None, description="Application status")
    application_date: Optional[str] = Field(None, description="Date application was submitted")
    documents_received: Optional[List[str]] = Field(None, description="Documents received")
    documents_pending: Optional[List[str]] = Field(None, description="Documents still needed")
    estimated_decision_date: Optional[str] = Field(None, description="Expected decision date")
    message: str = Field(..., description="Human-readable status message")

class InteractionSummary(BaseModel):
    """Summary of interaction for dashboard display"""
    id: str
    student_name: Optional[str]
    student_email: Optional[str]
    topic: str
    duration_seconds: int
    sentiment: str
    outcome: str
    timestamp: datetime
    # NEW: Transcript fields for Recent Conversations component
    transcript_json: Optional[List[Dict[str, Any]]] = None
    transcript_summary: Optional[str] = None
    transcript_preview: Optional[str] = None
    turn_count: Optional[int] = None
    user_turns: Optional[int] = None
    agent_turns: Optional[int] = None
    started_at: Optional[datetime] = None  # Alias for timestamp

class InteractionDetail(BaseModel):
    """Detailed interaction data including full transcript"""
    id: str
    student_name: Optional[str]
    student_email: Optional[str]
    topic: str
    duration_seconds: int
    sentiment: str
    outcome: str
    timestamp: datetime
    transcript: List[TranscriptEntry]
    summary: str

class AnalyticsSummary(BaseModel):
    """Analytics summary for dashboard"""
    total_conversations: int
    total_duration_minutes: int
    average_duration_seconds: int
    sentiment_breakdown: Dict[str, int]
    outcome_breakdown: Dict[str, int]
    top_topics: List[Dict[str, int]]
    hourly_distribution: List[int]

class EscalationRequest(BaseModel):
    """Request to create an escalation ticket"""
    student_name: str = Field(..., description="Student's full name")
    student_email: str = Field(..., description="Student's email address")
    student_phone: Optional[str] = Field(None, description="Student's phone number")
    inquiry_topic: str = Field(..., description="Brief description of the inquiry")
    best_time_to_call: Optional[str] = Field(None, description="Best time to contact student")
    conversation_id: Optional[str] = Field(None, description="Related conversation ID")

class EscalationResponse(BaseModel):
    """Response after creating escalation ticket"""
    escalation_id: str = Field(..., description="Unique escalation ticket ID")
    status: str = Field(..., description="Status of the escalation")
    message: str = Field(..., description="Human-readable confirmation message")
    estimated_response_time: str = Field(..., description="When student can expect follow-up")

class EscalationSummary(BaseModel):
    """Summary of escalation for dashboard display"""
    id: str
    student_name: str
    student_email: str
    student_phone: Optional[str]
    inquiry_topic: str
    best_time_to_call: Optional[str]
    conversation_id: Optional[str]
    created_at: datetime
    status: str  # 'pending', 'in_progress', 'resolved'
    assigned_to: Optional[str]
    priority: str  # Derived: 'urgent' (>24h), 'high' (>12h), 'medium' (else)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationListItem(BaseModel):
    """Conversation item for Conversations page list/table views"""
    id: str = Field(..., description="Unique conversation identifier")
    agent_id: str = Field(..., description="ElevenLabs agent ID")
    started_at: datetime = Field(..., description="Conversation start timestamp")
    duration: int = Field(..., description="Duration in seconds")
    messages_count: int = Field(0, description="Number of messages in conversation")
    evaluation_result: str = Field("successful", description="successful | needs_review | failed")
    outcome: str = Field("resolved", description="resolved | escalated | failed")
    user_name: Optional[str] = Field(None, description="User/student name if available")
    user_email: Optional[str] = Field(None, description="User/student email if available")
    topic: str = Field("General Inquiry", description="Conversation topic")
    sentiment: str = Field("neutral", description="Overall conversation sentiment")
    summary: Optional[str] = Field(None, description="Conversation summary")
    synced_at: Optional[datetime] = Field(None, description="When this conversation was last synced")
    source: str = Field("sync", description="sync | webhook")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message (for sorting)")
    # NEW: Transcript fields for detail modal
    transcript_json: Optional[List[Dict[str, Any]]] = Field(None, description="Full transcript array")
    transcript_summary: Optional[str] = Field(None, description="ElevenLabs AI-generated summary")
    transcript_preview: Optional[str] = Field(None, description="Short preview (first 100 chars)")
    turn_count: Optional[int] = Field(None, description="Total conversation turns")
    user_turns: Optional[int] = Field(None, description="User/student turns")
    agent_turns: Optional[int] = Field(None, description="Agent turns")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationsResponse(BaseModel):
    """Response for conversations list endpoint"""
    conversations: List[ConversationListItem] = Field(..., description="List of conversations")
    total_count: int = Field(..., description="Total conversations matching filters")
    filtered_count: int = Field(..., description="Number of conversations after filters applied")
    last_sync: Optional[datetime] = Field(None, description="Last time data was synced from ElevenLabs")
    page: int = Field(1, ge=1, description="Current page number (1-indexed)")
    limit: int = Field(50, ge=1, le=100, description="Items per page")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }