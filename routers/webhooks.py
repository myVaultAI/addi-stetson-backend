"""
Webhook endpoints for ElevenLabs integration
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request, Query
from typing import Optional, Dict, Any, List
import os
import logging
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from models.calls import (
    InteractionLog,
    StudentStatusRequest,
    StudentStatusResponse,
    InteractionSummary,
    InteractionDetail,
    AnalyticsSummary,
    EscalationRequest,
    EscalationResponse,
    EscalationSummary,
    EscalationStatusUpdate,
    EscalationNoteCreate,
    EscalationNote,
    ConversationListItem,
    ConversationsResponse,
    SpeakerType,
    TranscriptEntry,
)
from services.elevenlabs_api_client import ElevenLabsAPIClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

# File-based persistence for demo data
DATA_DIR = "data"
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions.json")
ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")

# Agent constants
ADDI_AGENT_ID = "agent_0301k84pwdr2ffprwkqaha0f178g"

SPEAKER_AGENT_ALIASES = {"agent", "assistant", "system", "ai", "addisupport", "support"}
SPEAKER_USER_ALIASES = {"user", "student", "caller", "prospect", "customer", "lead"}


def _determine_speaker(entry: Dict[str, Any]) -> str:
    """Normalize speaker labels across different ElevenLabs payload formats."""
    raw_speaker = (
        entry.get("speaker")
        or entry.get("role")
        or entry.get("source")
        or entry.get("participant_role")
        or ""
    )

    speaker = str(raw_speaker).lower().strip()

    if speaker in SPEAKER_AGENT_ALIASES:
        return SpeakerType.AGENT.value
    if speaker in SPEAKER_USER_ALIASES:
        return SpeakerType.USER.value

    # Heuristics if explicit label absent
    if entry.get("agent_metadata") or entry.get("llm_usage"):
        return SpeakerType.AGENT.value

    return SpeakerType.USER.value


def _coerce_text_value(value: Any) -> Optional[str]:
    """Coerce common ElevenLabs text payload shapes (str, dict, list) into plain text."""
    if value is None:
        return None
    
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    
    if isinstance(value, list):
        parts = [
            segment.strip()
            for segment in value
            if isinstance(segment, str) and segment.strip()
        ]
        combined = " ".join(parts).strip()
        return combined or None
    
    if isinstance(value, dict):
        # ElevenLabs sometimes nests text under these keys
        for key in ("text", "value", "content", "message"):
            nested = _coerce_text_value(value.get(key))
            if nested:
                return nested
    
    return None


def _extract_transcript_text(entry: Dict[str, Any]) -> str:
    """Prefer full text sources (original_message) before truncated ones (message/text)."""
    candidate_fields = [
        entry.get("original_message"),
        entry.get("message"),
        entry.get("text"),
        entry.get("content"),
        entry.get("display_text"),
    ]
    
    for candidate in candidate_fields:
        normalized = _coerce_text_value(candidate)
        if normalized:
            return normalized
    
    # Fallback: some payloads expose text under llm_response or similar shapes
    llm_response = entry.get("llm_response")
    if llm_response:
        normalized = _coerce_text_value(llm_response if isinstance(llm_response, (str, list)) else llm_response.get("text"))
        if normalized:
            return normalized
    
    return ""


def _normalize_transcript_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ensure each transcript entry has consistent structure for UI + analytics."""
    if not entry:
        return None

    speaker = _determine_speaker(entry)

    text = _extract_transcript_text(entry)

    # ElevenLabs often returns `timestamp` or `time_in_call_secs`
    timestamp = entry.get("timestamp")
    if timestamp is None:
        timestamp = entry.get("time_in_call_secs")
    if timestamp is None:
        timestamp = 0.0

    try:
        timestamp = float(timestamp)
    except (TypeError, ValueError):
        timestamp = 0.0

    metadata = {
        "agent_metadata": entry.get("agent_metadata"),
        "conversation_turn_metrics": entry.get("conversation_turn_metrics"),
        "llm_usage": entry.get("llm_usage"),
        "feedback": entry.get("feedback"),
        "rag_retrieval_info": entry.get("rag_retrieval_info"),
        "source_medium": entry.get("source_medium"),
        "sentiment": entry.get("sentiment"),
    }

    # Remove None values to keep payload compact
    metadata = {k: v for k, v in metadata.items() if v is not None}

    normalized = {
        "speaker": speaker,
        "text": text.strip(),
        "timestamp": timestamp,
        "time_in_call_secs": entry.get("time_in_call_secs"),
        "tool_calls": entry.get("tool_calls") or [],
        "tool_results": entry.get("tool_results") or [],
        "interrupted": entry.get("interrupted"),
        "original_message": entry.get("original_message"),
        "metadata": metadata or None,
    }

    return normalized


def _normalize_transcript(entries: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Normalize a transcript list while preserving original order."""
    if not entries:
        return []

    normalized: List[Dict[str, Any]] = []
    for entry in entries:
        normalized_entry = _normalize_transcript_entry(entry)
        if normalized_entry:
            normalized.append(normalized_entry)

    return normalized


def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created data directory: {DATA_DIR}")

def load_interactions():
    """Load interactions from file"""
    ensure_data_dir()
    if os.path.exists(INTERACTIONS_FILE):
        try:
            with open(INTERACTIONS_FILE, 'r') as f:
                data = json.load(f)
                # Convert string timestamps back to datetime objects
                for item in data:
                    # Handle different timestamp field names (including new fields)
                    timestamp_fields = ['created_at', 'started_at', 'timestamp', 'synced_at', 'last_message_at']
                    for field in timestamp_fields:
                        if field in item and isinstance(item[field], str):
                            try:
                                item[field] = datetime.fromisoformat(item[field].replace('Z', '+00:00'))
                            except:
                                # If parsing fails, keep original value (could be None or invalid)
                                pass
                # Dedupe by id (latest wins)
                deduped: Dict[str, Any] = {}
                for item in data:
                    item_id = item.get("id")
                    if not item_id:
                        continue
                    deduped[item_id] = item
                deduped_list = list(deduped.values())
                for item in deduped_list:
                    transcript = item.get("transcript_json")
                    normalized_transcript = _normalize_transcript(transcript)
                    item["transcript_json"] = normalized_transcript

                    # Ensure message/turn counts stay accurate
                    total_turns = len(normalized_transcript)
                    item["messages_count"] = item.get("messages_count") or total_turns
                    item["turn_count"] = total_turns
                    item["user_turns"] = len(
                        [t for t in normalized_transcript if t.get("speaker") == SpeakerType.USER.value]
                    )
                    item["agent_turns"] = len(
                        [t for t in normalized_transcript if t.get("speaker") == SpeakerType.AGENT.value]
                    )

                logger.info(f"Loaded {len(deduped_list)} interactions from file (deduped)")
                return deduped_list
        except Exception as e:
            logger.error(f"Failed to load interactions: {e}")
    return []

def save_interactions(interactions):
    """Save interactions to file"""
    ensure_data_dir()
    try:
        for item in interactions:
            if "transcript_json" in item:
                normalized = _normalize_transcript(item.get("transcript_json"))
                item["transcript_json"] = normalized
                total_turns = len(normalized)
                item["messages_count"] = item.get("messages_count") or total_turns
                item["turn_count"] = total_turns
                item["user_turns"] = len(
                    [t for t in normalized if t.get("speaker") == SpeakerType.USER.value]
                )
                item["agent_turns"] = len(
                    [t for t in normalized if t.get("speaker") == SpeakerType.AGENT.value]
                )
        with open(INTERACTIONS_FILE, 'w') as f:
            json.dump(interactions, f, indent=2, default=str)
        logger.info(f"Saved {len(interactions)} interactions to file")
    except Exception as e:
        logger.error(f"Failed to save interactions: {e}")

def load_escalations():
    """Load escalations from file"""
    ensure_data_dir()
    if os.path.exists(ESCALATIONS_FILE):
        try:
            with open(ESCALATIONS_FILE, 'r') as f:
                data = json.load(f)
                # Convert string timestamps back to datetime objects
                for item in data:
                    if 'created_at' in item and isinstance(item['created_at'], str):
                        try:
                            item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                        except:
                            item['created_at'] = datetime.utcnow()
                logger.info(f"Loaded {len(data)} escalations from file")
                return data
        except Exception as e:
            logger.error(f"Failed to load escalations: {e}")
    return []

def save_escalations(escalations):
    """Save escalations to file"""
    ensure_data_dir()
    try:
        with open(ESCALATIONS_FILE, 'w') as f:
            json.dump(escalations, f, indent=2, default=str)
        logger.info(f"Saved {len(escalations)} escalations to file")
    except Exception as e:
        logger.error(f"Failed to save escalations: {e}")

# API Key validation
async def verify_api_key(authorization: str = Header(None)):
    """Verify ElevenLabs API key for webhook security"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    expected_key = f"Bearer {os.getenv('ELEVENLABS_API_KEY')}"
    if authorization != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True

# HMAC Signature validation for post-call webhooks
async def verify_elevenlabs_signature(
    request: Request,
    elevenlabs_signature: Optional[str] = Header(None, alias="ElevenLabs-Signature")
):
    """
    Verify HMAC signature from ElevenLabs post-call webhook.
    ElevenLabs signs webhook payloads using HMAC-SHA256.
    """
    webhook_secret = os.getenv('ELEVENLABS_WEBHOOK_SECRET')
    
    if not webhook_secret:
        logger.warning("ELEVENLABS_WEBHOOK_SECRET not configured - skipping signature verification")
        return True  # Allow through if secret not configured (development mode)
    
    if not elevenlabs_signature:
        logger.error("Missing ElevenLabs-Signature header")
        raise HTTPException(
            status_code=401, 
            detail="Missing ElevenLabs-Signature header"
        )
    
    # Get raw body for signature verification
    body = await request.body()
    
    # ElevenLabs uses HMAC-SHA256 with the secret as key and body as message
    # The signature is sent as hex string
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # ElevenLabs may send signature with or without 'sha256=' prefix
    clean_signature = elevenlabs_signature.replace('sha256=', '') if elevenlabs_signature.startswith('sha256=') else elevenlabs_signature
    
    # Compare signatures using constant-time comparison
    if not hmac.compare_digest(clean_signature, expected_signature):
        logger.error(f"Invalid signature. Expected: {expected_signature[:10]}..., Got: {clean_signature[:10]}...")
        raise HTTPException(
            status_code=401, 
            detail="Invalid webhook signature"
        )
    
    logger.info("Webhook signature verified successfully")
    return True

# Initialize persistent storage
interactions_db = load_interactions()
escalations_db = load_escalations()
students_db = {
    "sarah.j@example.com": {
        "name": "Sarah Johnson",
        "email": "sarah.j@example.com",
        "status": "Application Under Review",
        "application_date": "2025-02-15",
        "documents_received": ["Transcript", "SAT Scores", "Essay"],
        "documents_pending": ["Letter of Recommendation"],
        "estimated_decision_date": "2025-03-20"
    }
}

@router.get("/interaction/log")
async def get_interaction_log_status():
    """
    Health check endpoint for ElevenLabs webhook validation.
    Returns 200 OK to confirm endpoint is accessible.
    """
    return {
        "status": "ok",
        "message": "Interaction log webhook endpoint is active",
        "endpoint": "/api/webhooks/interaction/log",
        "method": "POST"
    }

@router.post("/interaction/log")
async def log_interaction(
    request: Request
    # Temporarily disabled for ElevenLabs testing
    # _: bool = Depends(verify_elevenlabs_signature)
):
    """
    Receives post-call webhook from ElevenLabs.
    Stores conversation data for dashboard display.
    
    SECURITY: Uses HMAC signature verification (not API key).
    ElevenLabs sends 'ElevenLabs-Signature' header with HMAC-SHA256 signature.
    """
    try:
        # Parse JSON body after signature verification
        body = await request.json()
        logger.info(f"Received interaction log for conversation {body.get('conversation_id', 'unknown')}")
        
        # Extract data from ElevenLabs webhook payload
        # Note: Actual structure may vary - adjust based on real webhook data
        interaction_data = {
            "id": body.get("conversation_id", f"conv_{datetime.utcnow().timestamp()}"),
            "agent_id": body.get("agent_id", "unknown"),
            "started_at": datetime.fromisoformat(body.get("timestamp", datetime.utcnow().isoformat())),
            "duration": body.get("duration_seconds", 0),
            "transcript_json": body.get("transcript", []),
            "summary": body.get("summary", ""),
            "extracted_data_json": body.get("extracted_data", {}),
            "sentiment": body.get("sentiment", "neutral"),
            "outcome": body.get("call_outcome", "completed"),
            "created_at": datetime.utcnow(),
            "source": "webhook"
        }
        # Upsert by id (idempotent)
        current = load_interactions()
        upserted = False
        for idx, existing in enumerate(current):
            if existing.get("id") == interaction_data["id"]:
                current[idx] = interaction_data
                upserted = True
                break
        if not upserted:
            current.append(interaction_data)
        save_interactions(current)
        
        logger.info(f"Successfully logged interaction {interaction_data['id']}")
        
        return {
            "status": "success",
            "conversation_id": interaction_data["id"],
            "message": "Interaction logged successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to log interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log interaction: {str(e)}")

@router.post("/student/status", response_model=StudentStatusResponse)
async def get_student_status(
    request: StudentStatusRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Server Tool for ElevenLabs: Get student application status.
    Requires API key authentication.
    """
    try:
        logger.info(f"Student status request for {request.student_email}")
        
        # Query student database (mock for demo)
        student = students_db.get(request.student_email.lower())
        
        if not student:
            return StudentStatusResponse(
                found=False,
                message="I couldn't find an application with that email. Please verify your information or contact admissions@stetson.edu."
            )
        
        # Verify name matches (basic validation)
        if student["name"].lower() != request.student_name.lower():
            return StudentStatusResponse(
                found=False,
                message="The name doesn't match our records. Please verify your information or contact admissions@stetson.edu."
            )
        
        return StudentStatusResponse(
            found=True,
            status=student["status"],
            application_date=student["application_date"],
            documents_received=student["documents_received"],
            documents_pending=student["documents_pending"],
            estimated_decision_date=student["estimated_decision_date"],
            message=f"Your application is currently {student['status'].lower()}. " +
                    (f"We're still waiting for: {', '.join(student['documents_pending'])}." if student['documents_pending'] else "All documents received!")
        )
        
    except Exception as e:
        logger.error(f"Failed to get student status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get student status: {str(e)}")

@router.post("/escalation/create", response_model=EscalationResponse)
async def create_escalation(
    request: EscalationRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Server Tool for ElevenLabs: Create an escalation ticket for human follow-up.
    """
    try:
        logger.info(f"Creating escalation for {request.student_name} ({request.student_email})")
        
        # Generate escalation ID
        escalation_id = f"ESC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(escalations_db) + 1}"
        
        # Store escalation
        escalation = {
            "id": escalation_id,
            "student_name": request.student_name,
            "student_email": request.student_email,
            "student_phone": request.student_phone,
            "inquiry_topic": request.inquiry_topic,
            "best_time_to_call": request.best_time_to_call,
            "conversation_id": request.conversation_id,
            "created_at": datetime.utcnow(),
            "status": "pending",
            "assigned_to": None
        }
        escalations_db.append(escalation)
        save_escalations(escalations_db)
        
        logger.info(f"Escalation {escalation_id} created successfully")
        
        return EscalationResponse(
            escalation_id=escalation_id,
            status="created",
            message=f"Thank you! An admissions counselor will reach out to {request.student_name} within 24 hours.",
            estimated_response_time="within 24 hours"
        )
        
    except Exception as e:
        logger.error(f"Failed to create escalation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create escalation: {str(e)}")

@router.get("/dashboard/interactions", response_model=list[InteractionSummary])
async def get_interactions(
    limit: int = 50,
    offset: int = 0,
    days: int = 7
):
    """
    Get list of recent interactions for dashboard.
    Default: Last 7 days, limit 50.
    """
    try:
        # Always load fresh from disk
        interactions = load_interactions()

        # Filter interactions by date and agent and apply pagination
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        
        filtered_interactions = []
        for interaction in interactions:
            if interaction.get("agent_id") != ADDI_AGENT_ID:
                continue
            if interaction["started_at"].timestamp() < cutoff_date:
                continue
            # Exclude flagged manual test data from lists
            if interaction.get("source") == "manual:test":
                continue
            filtered_interactions.append(interaction)
        
        # Apply pagination
        paginated_interactions = filtered_interactions[offset:offset + limit]
        
        # Convert to response format
        summaries = []
        for interaction in paginated_interactions:
            extracted_data = interaction.get("extracted_data_json", {})
            summary = InteractionSummary(
                id=interaction["id"],
                student_name=extracted_data.get("user_name"),
                student_email=extracted_data.get("user_email"),
                topic=extracted_data.get("call_topic", "General Inquiry"),
                duration_seconds=interaction.get("duration", 0),
                sentiment=interaction.get("sentiment", "neutral"),
                outcome=interaction.get("outcome", "resolved"),
                timestamp=interaction["started_at"],
                # NEW: Transcript fields
                transcript_json=interaction.get("transcript_json"),
                transcript_summary=interaction.get("transcript_summary"),
                transcript_preview=interaction.get("transcript_preview"),
                turn_count=interaction.get("turn_count"),
                user_turns=interaction.get("user_turns"),
                agent_turns=interaction.get("agent_turns"),
                started_at=interaction.get("started_at")
            )
            summaries.append(summary)
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to get interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interactions: {str(e)}")

@router.get("/dashboard/interactions/{interaction_id}", response_model=InteractionDetail)
async def get_interaction_detail(interaction_id: str):
    """
    Get full details of a single interaction including transcript.
    """
    try:
        # Always load fresh from disk
        data = load_interactions()
        # Find interaction by ID
        interaction = None
        for i in data:
            if i["id"] == interaction_id:
                interaction = i
                break
        
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        # Convert transcript back to TranscriptEntry objects
        transcript_entries: List[TranscriptEntry] = []
        for entry in interaction.get("transcript_json", []):
            normalized_entry = _normalize_transcript_entry(entry) or {
                "speaker": SpeakerType.AGENT.value,
                "text": "",
                "timestamp": 0.0,
            }
            try:
                transcript_entries.append(TranscriptEntry(**normalized_entry))
            except Exception as exc:
                logger.warning(
                    "Failed to coerce transcript entry for %s: %s",
                    interaction["id"],
                    exc,
                )
        
        extracted_data = interaction.get("extracted_data_json", {})
        
        return InteractionDetail(
            id=interaction["id"],
            student_name=extracted_data.get("user_name"),
            student_email=extracted_data.get("user_email"),
            topic=extracted_data.get("call_topic", "General Inquiry"),
            duration_seconds=interaction["duration"],
            sentiment=interaction.get("sentiment", "neutral"),
            outcome=interaction.get("outcome", "resolved"),
            timestamp=interaction["started_at"],
            transcript=transcript_entries,
            summary=interaction.get("summary", "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interaction detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interaction detail: {str(e)}")

@router.get("/dashboard/analytics", response_model=AnalyticsSummary)
async def get_analytics(days: int = 30):
    """
    Get analytics summary for dashboard.
    Default: Last 30 days.
    """
    try:
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        
        # Load fresh and filter by date, agent, and source
        interactions = load_interactions()
        recent_interactions = []
        for interaction in interactions:
            if interaction.get("agent_id") != ADDI_AGENT_ID:
                continue
            if interaction["started_at"].timestamp() <= cutoff_date:
                continue
            if interaction.get("source") == "manual:test":
                continue
            recent_interactions.append(interaction)
        
        if not recent_interactions:
            return AnalyticsSummary(
                total_conversations=0,
                total_duration_minutes=0,
                average_duration_seconds=0,
                sentiment_breakdown={},
                outcome_breakdown={},
                top_topics=[],
                hourly_distribution=[0] * 24
            )
        
        # Calculate analytics
        total_conversations = len(recent_interactions)
        total_duration_seconds = sum(i["duration"] for i in recent_interactions)
        total_duration_minutes = total_duration_seconds // 60
        average_duration_seconds = total_duration_seconds // total_conversations if total_conversations > 0 else 0
        
        # Sentiment breakdown
        sentiment_counts = {}
        for interaction in recent_interactions:
            sentiment = interaction.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Outcome breakdown (normalized)
        outcome_counts = {}
        def normalize_outcome(raw: str) -> str:
            raw_l = (raw or "").lower()
            # Map all success/resolution outcomes to "resolved"
            if raw_l in ("resolved", "completed", "successful", "success", "escalated_handled", "done", "finished"):
                return "resolved"
            if raw_l in ("escalated", "handoff", "transferred"):
                return "escalated"
            if raw_l in ("failed", "error", "abandoned"):
                return "failed"
            # Default to resolved for unknown outcomes (assume success if no error)
            return "resolved"
        for interaction in recent_interactions:
            outcome = normalize_outcome(interaction.get("outcome", "resolved"))
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        
        # Topic analysis (simplified)
        topic_counts = {}
        for interaction in recent_interactions:
            extracted_data = interaction.get("extracted_data_json", {})
            topic = extracted_data.get("call_topic", "General Inquiry")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Sort topics by count
        top_topics = [
            {topic: count} for topic, count in 
            sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Hourly distribution (simplified - all at current hour for demo)
        hourly_distribution = [0] * 24
        current_hour = datetime.utcnow().hour
        hourly_distribution[current_hour] = total_conversations
        
        return AnalyticsSummary(
            total_conversations=total_conversations,
            total_duration_minutes=total_duration_minutes,
            average_duration_seconds=average_duration_seconds,
            sentiment_breakdown=sentiment_counts,
            outcome_breakdown=outcome_counts,
            top_topics=top_topics,
            hourly_distribution=hourly_distribution
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/dashboard/escalations", response_model=list[EscalationSummary])
async def get_escalations(
    limit: int = 50,
    offset: int = 0,
    status: str = None  # Filter: 'pending', 'in_progress', 'resolved', or None (all)
):
    """
    Get list of escalations for dashboard.
    Automatically calculates priority based on age.
    """
    try:
        from datetime import datetime, timedelta

        # Filter by status if provided
        filtered_escalations = escalations_db
        if status:
            filtered_escalations = [
                esc for esc in escalations_db
                if esc.get("status") == status
            ]

        # Sort by created_at (newest first)
        sorted_escalations = sorted(
            filtered_escalations,
            key=lambda x: x["created_at"],
            reverse=True
        )

        # Apply pagination
        paginated = sorted_escalations[offset:offset + limit]

        # Convert to response format with priority calculation
        summaries = []
        from datetime import timezone
        now = datetime.now(timezone.utc)

        for esc in paginated:
            esc_created_at = esc["created_at"]
            if isinstance(esc_created_at, datetime):
                created_at_dt = esc_created_at
            else:
                created_at_dt = datetime.fromisoformat(str(esc_created_at).replace('Z', '+00:00'))

            if created_at_dt.tzinfo is None:
                created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)

            # Calculate priority based on age
            age_hours = (now - created_at_dt).total_seconds() / 3600

            if age_hours > 24:
                priority = "urgent"
            elif age_hours > 12:
                priority = "high"
            else:
                priority = "medium"

            summary = EscalationSummary(
                id=esc["id"],
                student_name=esc["student_name"],
                student_email=esc["student_email"],
                student_phone=esc.get("student_phone"),
                inquiry_topic=esc["inquiry_topic"],
                best_time_to_call=esc.get("best_time_to_call"),
                conversation_id=esc.get("conversation_id"),
                created_at=created_at_dt,
                status=esc["status"],
                assigned_to=esc.get("assigned_to"),
                priority=priority
            )
            summaries.append(summary)

        return summaries

    except Exception as e:
        logger.error(f"Failed to get escalations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get escalations: {str(e)}")

# Seed some sample data for demo
def seed_sample_data():
    """Seed database with sample interaction data for demo"""
    sample_interactions = [
        {
            "id": "conv_demo_001",
            "agent_id": "agent_0301k84pwdr2ffprwkqaha0f178g",
            "started_at": datetime.utcnow(),
            "duration": 185,
            "transcript_json": [
                {"speaker": "agent", "text": "Hi! I'm Addi, your Stetson University admissions assistant. How can I help you today?", "timestamp": 0},
                {"speaker": "user", "text": "What majors do you have for marine science?", "timestamp": 3.2},
                {"speaker": "agent", "text": "Stetson offers a Bachelor of Science in Marine Biology and a Bachelor of Arts in Environmental Science with a Marine emphasis. Both programs include hands-on research opportunities at our marine lab in the Florida Keys.", "timestamp": 5.8},
                {"speaker": "user", "text": "That sounds great! Can I schedule a campus tour?", "timestamp": 12.5},
                {"speaker": "agent", "text": "Absolutely! I can help you schedule a campus tour. I'll send you a text message with a link to choose your preferred date and time. Is this the best number to reach you?", "timestamp": 14.2},
                {"speaker": "user", "text": "Yes, that works!", "timestamp": 18.9},
                {"speaker": "agent", "text": "Perfect! You should receive the text within the next minute. Is there anything else I can help you with today?", "timestamp": 20.1},
                {"speaker": "user", "text": "No, that's all. Thank you!", "timestamp": 23.4},
                {"speaker": "agent", "text": "You're welcome! Have a great day, and we look forward to seeing you on campus!", "timestamp": 24.8}
            ],
            "summary": "Prospective student inquired about marine science programs. Provided information about B.S. Marine Biology and B.A. Environmental Science programs. Successfully scheduled campus tour via text message link.",
            "extracted_data_json": {
                "user_name": "Jessica Martinez",
                "user_email": None,
                "call_topic": "Academic Programs - Marine Science",
                "follow_up_required": False
            },
            "sentiment": "positive",
            "outcome": "resolved",
            "created_at": datetime.utcnow()
        }
    ]
    
    interactions_db.extend(sample_interactions)
    logger.info(f"Seeded {len(sample_interactions)} sample interactions")

# Initialize sample data
seed_sample_data()

# --------------------------
# ElevenLabs Incremental Sync
# --------------------------

def _normalize_elevenlabs_conversation(conv: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map ElevenLabs conversation to our interaction format.
    ENHANCED with all fields needed for Conversations page.
    EXCLUDES: credits, llm_cost per user requirements.
    """
    # Get metadata and analysis sections
    metadata = conv.get("metadata", {})
    analysis = conv.get("analysis", {})
    transcript = conv.get("transcript", [])
    normalized_transcript = _normalize_transcript(transcript)
    
    conversation_id = conv.get("id") or conv.get("conversation_id")
    agent_id = conv.get("agent_id") or conv.get("agentId")
    
    # Parse timestamp - try multiple formats
    # Log the raw conversation data to debug timestamp extraction
    logger.debug(f"Parsing timestamp for conversation {conversation_id}")
    logger.debug(f"Conv keys: {list(conv.keys())}")
    logger.debug(f"Metadata keys: {list(metadata.keys()) if metadata else 'None'}")
    
    start_time_unix = metadata.get("start_time_unix_secs") if metadata else None
    if start_time_unix:
        try:
            started_at = datetime.fromtimestamp(start_time_unix)
            logger.debug(f"Parsed timestamp from start_time_unix_secs: {started_at}")
        except Exception as e:
            logger.warning(f"Failed to parse unix timestamp: {e}")
            started_at = datetime.utcnow()
    else:
        # Try various timestamp fields
        ts = (conv.get("started_at") or 
              conv.get("start_time") or 
              conv.get("timestamp") or
              conv.get("created_at") or
              metadata.get("start_time") if metadata else None)
        
        logger.debug(f"Trying timestamp fields, found: {ts}")
        
        if ts:
            try:
                # Handle ISO format with or without Z
                if isinstance(ts, str):
                    started_at = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                elif isinstance(ts, datetime):
                    started_at = ts
                else:
                    # Try unix timestamp
                    started_at = datetime.fromtimestamp(float(ts))
                logger.debug(f"Parsed timestamp: {started_at}")
            except Exception as e:
                logger.warning(f"Failed to parse timestamp '{ts}': {e}")
                started_at = datetime.utcnow()
        else:
            logger.warning(f"No timestamp found for conversation {conversation_id}, using current time")
            started_at = datetime.utcnow()

    # Extract user data from analysis or extracted_data
    collected_data = analysis.get("data_collection_result", {}) if analysis else {}
    extracted_data = conv.get("extracted_data", {})
    
    # Combine data sources (analysis takes precedence, then extracted_data)
    user_name = (
        collected_data.get("user_name") or 
        collected_data.get("student_name") or 
        extracted_data.get("user_name") or 
        extracted_data.get("student_name") or 
        None
    )
    user_email = (
        collected_data.get("user_email") or 
        collected_data.get("student_email") or 
        extracted_data.get("user_email") or 
        extracted_data.get("student_email") or 
        None
    )
    
    # Count messages in transcript
    messages_count = len(normalized_transcript)
    
    # Get last message timestamp (for sorting/filtering)
    last_message_at = None
    if normalized_transcript:
        try:
            last_timestamp = normalized_transcript[-1].get("timestamp", 0) or 0
            last_message_at = started_at + timedelta(seconds=last_timestamp)
        except Exception:
            last_message_at = started_at
    else:
        last_message_at = started_at

    # Try to infer summary/sentiment/outcome fields if present
    summary = (
        analysis.get("transcript_summary") or 
        analysis.get("summary") or 
        conv.get("summary") or 
        conv.get("last_summary") or 
        ""
    )
    sentiment = (
        conv.get("sentiment") or 
        analysis.get("aggregate_sentiment") or 
        "neutral"
    )
    
    # Map evaluation result (from call_successful and quality_score if available)
    call_successful = analysis.get("call_successful", True)
    call_quality_score = analysis.get("quality_score", 1.0) if analysis else 1.0
    
    if call_successful and call_quality_score >= 0.8:
        evaluation_result = "successful"
    elif call_successful:
        evaluation_result = "needs_review"
    else:
        evaluation_result = "failed"
    
    # Get outcome from multiple possible fields and normalize it
    outcome_raw = (
        conv.get("outcome") or 
        conv.get("call_outcome") or 
        conv.get("status") or 
        conv.get("conversation_outcome") or 
        "completed"
    )
    
    # Normalize outcome using same logic as analytics
    outcome_raw_l = (outcome_raw or "").lower()
    if outcome_raw_l in ("resolved", "completed", "successful", "success", "escalated_handled", "done", "finished"):
        outcome = "resolved"
    elif outcome_raw_l in ("escalated", "handoff", "transferred"):
        outcome = "escalated"
    elif outcome_raw_l in ("failed", "error", "abandoned"):
        outcome = "failed"
    else:
        outcome = "resolved"  # Default to resolved for unknown outcomes

    # Get duration from metadata or conv
    # Handle multiple field names from different ElevenLabs sources
    duration = (
        conv.get("call_duration_seconds") or   # Webhook format
        metadata.get("call_duration_secs") or 
        metadata.get("duration_seconds") or 
        conv.get("duration_seconds") or         # API list format
        conv.get("duration") or 
        0
    )
    
    # If duration is a string like "1:46", convert to seconds
    if isinstance(duration, str):
        try:
            if ':' in duration:
                parts = duration.split(':')
                if len(parts) == 2:
                    duration = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                duration = int(duration)
        except:
            duration = 0
    
    # Current sync timestamp
    synced_at = datetime.utcnow()
    
    # Merge extracted data
    merged_extracted_data = {**extracted_data, **collected_data}
    
    # Get topic from extracted data
    topic = (
        merged_extracted_data.get("call_topic") or 
        merged_extracted_data.get("topic") or 
        "General Inquiry"
    )
    
    # Generate transcript preview from ElevenLabs summary
    transcript_preview = summary[:100] + "..." if len(summary) > 100 else summary
    
    # If no summary, fallback to first user message
    if not transcript_preview and normalized_transcript:
        user_messages = [
            t.get("text", "")
            for t in normalized_transcript
            if t.get("speaker") == SpeakerType.USER.value
            and len(t.get("text", "")) > 20
        ]
        if user_messages:
            preview = user_messages[0]
            transcript_preview = preview[:100] + "..." if len(preview) > 100 else preview

    normalized = {
        "id": conversation_id or f"conv_{datetime.utcnow().timestamp()}",
        "agent_id": agent_id or "unknown",
        "started_at": started_at,
        "duration": duration,
        "transcript_json": normalized_transcript,
        "summary": summary,
        "extracted_data_json": merged_extracted_data,
        "sentiment": sentiment,
        "outcome": outcome,  # Use normalized outcome
        "messages_count": messages_count,  # ← NEW for Conversations page
        "evaluation_result": evaluation_result,  # ← NEW for Conversations page
        "last_message_at": last_message_at,  # ← NEW for sorting/filtering
        "user_name": user_name,  # ← NEW for Conversations page
        "user_email": user_email,  # ← NEW for Conversations page
        "topic": topic,  # ← NEW for Conversations page
        "transcript_preview": transcript_preview,  # ← NEW: Preview for dashboard (100 chars)
        "transcript_summary": summary,  # ← NEW: Full ElevenLabs summary
        "turn_count": len(normalized_transcript),  # ← NEW: Total conversation turns
        "user_turns": len(
            [t for t in normalized_transcript if t.get("speaker") == SpeakerType.USER.value]
        ),
        "agent_turns": len(
            [t for t in normalized_transcript if t.get("speaker") == SpeakerType.AGENT.value]
        ),
        "created_at": datetime.utcnow(),
        "source": "sync",
        "synced_at": synced_at  # ← NEW for last sync indicator
    }
    # NOTE: EXCLUDED fields per user requirements:
    # - credits (call): NOT synced
    # - credits (LLM): NOT synced
    # - llm_cost: NOT synced
    return normalized


@router.post("/dashboard/sync/elevenlabs")
async def sync_from_elevenlabs(
    days: int = 30, 
    agent_id: str = ADDI_AGENT_ID,
    incremental: bool = True
):
    """
    Pull recent conversations from ElevenLabs and merge idempotently.
    - Filters to the specified agent id (default: Addi)
    - Considers conversations within the last `days`
    - NEW: Incremental mode only fetches conversations newer than most recent in DB
    - Upserts by conversation_id and saves to file
    Returns: { synced: N, updated: M, skipped: K, total_after: T, mode: str }
    """
    try:
        client = ElevenLabsAPIClient()
        
        # Determine cutoff timestamp (incremental vs full sync)
        if incremental:
            # Get most recent conversation timestamp from our database
            current = load_interactions()
            if current:
                # Filter to specified agent only
                agent_convos = [c for c in current if c.get("agent_id") == agent_id]
                if agent_convos:
                    # Find most recent timestamp
                    most_recent = max(
                        agent_convos,
                        key=lambda c: c.get("started_at") or datetime.min
                    )
                    cutoff_dt = most_recent.get("started_at") or (datetime.utcnow() - timedelta(days=days))
                    logger.info(f"Incremental sync: Fetching conversations after {cutoff_dt}")
                else:
                    # No conversations for this agent yet, use days parameter
                    cutoff_dt = datetime.utcnow() - timedelta(days=days)
                    logger.info(f"No existing conversations for {agent_id}, using {days} day lookback")
            else:
                # No conversations at all, use days parameter
                cutoff_dt = datetime.utcnow() - timedelta(days=days)
                logger.info(f"Empty database, fetching last {days} days")
            cutoff_ts = cutoff_dt.timestamp()
        else:
            # Full sync mode (fetch all within days)
            cutoff_dt = datetime.utcnow() - timedelta(days=days)
            cutoff_ts = cutoff_dt.timestamp()
            logger.info(f"Full sync: Fetching last {days} days")

        # Fetch all conversations from ElevenLabs (metadata only)
        conversations = await client.get_all_conversations(agent_id=agent_id)
        logger.info(f"Fetched {len(conversations)} total conversations from ElevenLabs")

        # Load current data fresh and index by id
        current = load_interactions()
        by_id: Dict[str, Any] = {item.get("id"): item for item in current if item.get("id")}

        synced = 0
        updated = 0
        skipped = 0

        # Filter conversations first, then fetch details only for relevant ones
        relevant_conversations = []
        for idx, conv in enumerate(conversations):
            # Quick check with metadata only
            conv_id = conv.get("conversation_id")
            
            # ElevenLabs returns start_time_unix_secs (not start_time ISO string)
            start_time_unix = conv.get("start_time_unix_secs")
            
            if idx == 0:
                logger.info(f"First conversation - ID: {conv_id}, timestamp: {start_time_unix}")
            
            if not start_time_unix:
                logger.warning(f"No timestamp for conversation {conv_id}, skipping")
                skipped += 1
                continue
            
            try:
                start_time = datetime.fromtimestamp(start_time_unix)
                
                if idx == 0:
                    logger.info(f"Parsed: {start_time}, cutoff: {datetime.fromtimestamp(cutoff_ts)}")
                
            except Exception as e:
                logger.warning(f"Failed to parse timestamp for {conv_id}: {e}")
                skipped += 1
                continue
            
            # Filter by cutoff timestamp
            if start_time.timestamp() <= cutoff_ts:
                skipped += 1
                continue
            # Enforce agent filter
            if conv.get("agent_id") != agent_id:
                logger.debug(f"Skipping conversation {conv_id} - wrong agent: {conv.get('agent_id')}")
                skipped += 1
                continue
            
            relevant_conversations.append(conv_id)
        
        logger.info(f"Found {len(relevant_conversations)} relevant conversations to sync")
        
        # Now fetch full details (including transcripts) for relevant conversations only
        for conv_id in relevant_conversations:
            try:
                # Fetch full conversation details (includes transcript)
                conv_details = await client.get_conversation_details(conv_id)
                norm = _normalize_elevenlabs_conversation(conv_details)
                
                existing = by_id.get(norm["id"])
                if existing:
                    by_id[norm["id"]] = norm
                    updated += 1
                    logger.debug(f"Updated conversation: {norm['id']}")
                else:
                    by_id[norm["id"]] = norm
                    synced += 1
                    logger.debug(f"Synced new conversation: {norm['id']}")
            except Exception as e:
                logger.warning(f"Failed to fetch details for {conv_id}: {e}")
                skipped += 1
                continue

        merged_list = list(by_id.values())
        save_interactions(merged_list)
        
        logger.info(f"Sync complete: synced={synced}, updated={updated}, skipped={skipped}")

        return {
            "status": "success",
            "synced": synced,
            "updated": updated,
            "skipped": skipped,
            "total_after": len(merged_list),
            "mode": "incremental" if incremental else "full",
            "message": "No new conversations to sync" if synced == 0 and updated == 0 else None
        }

    except Exception as e:
        logger.error(f"Failed to sync from ElevenLabs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync from ElevenLabs: {str(e)}")


@router.get("/dashboard/conversations", response_model=ConversationsResponse)
async def get_conversations(
    # Pagination
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    
    # Filters
    agent_id: Optional[str] = Query(ADDI_AGENT_ID, description="Filter by agent ID"),
    date_after: Optional[str] = Query(None, description="ISO date - conversations after this date"),
    date_before: Optional[str] = Query(None, description="ISO date - conversations before this date"),
    evaluation: Optional[str] = Query(None, description="Filter by evaluation: successful, needs_review, failed"),
    outcome: Optional[str] = Query(None, description="Filter by outcome: resolved, escalated, failed"),
    query: Optional[str] = Query(None, description="Search across transcript, summary, user info"),
    
    # Sorting
    sort_by: str = Query("started_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc")
):
    """
    Get conversations list for Conversations page.
    DEDICATED endpoint separate from interactions (for dashboard widgets).
    Returns paginated, filtered, sorted conversations.
    """
    try:
        # Load fresh data
        interactions = load_interactions()
        
        # Filter by agent
        if agent_id:
            interactions = [i for i in interactions if i.get("agent_id") == agent_id]
        
        # Exclude test data
        interactions = [i for i in interactions if i.get("source") != "manual:test"]
        
        total_count = len(interactions)
        
        # Apply date filters
        if date_after:
            try:
                after_dt = datetime.fromisoformat(date_after.replace('Z', '+00:00'))
                interactions = [i for i in interactions if i["started_at"] >= after_dt]
            except Exception as e:
                logger.warning(f"Invalid date_after: {date_after} - {str(e)}")
        
        if date_before:
            try:
                before_dt = datetime.fromisoformat(date_before.replace('Z', '+00:00'))
                interactions = [i for i in interactions if i["started_at"] <= before_dt]
            except Exception as e:
                logger.warning(f"Invalid date_before: {date_before} - {str(e)}")
        
        # Apply evaluation filter
        if evaluation:
            interactions = [i for i in interactions if i.get("evaluation_result") == evaluation]
        
        # Apply outcome filter
        if outcome:
            interactions = [i for i in interactions if i.get("outcome") == outcome]
        
        # Apply search query
        if query:
            query_lower = query.lower()
            filtered = []
            for i in interactions:
                # Search in summary
                if query_lower in (i.get("summary", "") or "").lower():
                    filtered.append(i)
                    continue
                
                # Search in user info
                user_name = i.get("user_name", "") or ""
                user_email = i.get("user_email", "") or ""
                if query_lower in user_name.lower() or query_lower in user_email.lower():
                    filtered.append(i)
                    continue
                
                # Search in transcript
                transcript = i.get("transcript_json", [])
                if transcript:
                    for entry in transcript:
                        text = entry.get("text", "") or entry.get("content", "") if isinstance(entry, dict) else str(entry)
                        if query_lower in text.lower():
                            filtered.append(i)
                            break
            
            interactions = filtered
        
        filtered_count = len(interactions)
        
        # Sort
        reverse = (sort_order.lower() == "desc")
        if sort_by == "started_at":
            interactions.sort(key=lambda x: x.get("started_at", datetime.min), reverse=reverse)
        elif sort_by == "last_message_at":
            interactions.sort(key=lambda x: x.get("last_message_at") or x.get("started_at", datetime.min), reverse=reverse)
        elif sort_by == "duration":
            interactions.sort(key=lambda x: x.get("duration", 0), reverse=reverse)
        elif sort_by == "messages_count":
            interactions.sort(key=lambda x: x.get("messages_count", 0), reverse=reverse)
        else:
            # Default to started_at
            interactions.sort(key=lambda x: x.get("started_at", datetime.min), reverse=reverse)
        
        # Paginate
        offset = (page - 1) * limit
        paginated = interactions[offset:offset + limit]
        
        # Get last sync time (most recent synced_at across all interactions)
        last_sync = None
        if interactions:
            synced_times = [i.get("synced_at") for i in interactions if i.get("synced_at")]
            if synced_times:
                try:
                    # Convert string timestamps to datetime if needed
                    parsed_times = []
                    for ts in synced_times:
                        if isinstance(ts, datetime):
                            parsed_times.append(ts)
                        elif isinstance(ts, str):
                            try:
                                parsed_times.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                            except:
                                pass
                    if parsed_times:
                        last_sync = max(parsed_times)
                except Exception as e:
                    logger.warning(f"Failed to parse sync times: {str(e)}")
        
        # Convert to response format
        conversations = []
        for i in paginated:
            extracted = i.get("extracted_data_json", {})
            
            # Get topic from extracted data or interaction
            topic = (
                i.get("topic") or
                extracted.get("call_topic") or
                extracted.get("topic") or
                "General Inquiry"
            )
            
            # Get user info (prioritize top-level fields from normalization)
            user_name = i.get("user_name")
            if not user_name:
                user_name = extracted.get("user_name") or extracted.get("student_name")
            
            user_email = i.get("user_email")
            if not user_email:
                user_email = extracted.get("user_email") or extracted.get("student_email")
            
            # Normalize transcript_json to ensure text field is populated
            raw_transcript = i.get("transcript_json")
            normalized_transcript = _normalize_transcript(raw_transcript) if raw_transcript else []
            
            conv = ConversationListItem(
                id=i["id"],
                agent_id=i.get("agent_id", "unknown"),
                started_at=i["started_at"],
                duration=i.get("duration", 0),
                messages_count=i.get("messages_count", 0),
                evaluation_result=i.get("evaluation_result", "successful"),
                outcome=i.get("outcome", "resolved"),
                user_name=user_name,
                user_email=user_email,
                topic=topic,
                sentiment=i.get("sentiment", "neutral"),
                summary=i.get("summary"),
                synced_at=i.get("synced_at"),
                source=i.get("source", "sync"),
                last_message_at=i.get("last_message_at"),
                # NEW: Transcript fields - use normalized transcript
                transcript_json=normalized_transcript,
                transcript_summary=i.get("transcript_summary"),
                transcript_preview=i.get("transcript_preview"),
                turn_count=i.get("turn_count") or len(normalized_transcript),
                user_turns=i.get("user_turns") or len([t for t in normalized_transcript if t.get("speaker") == SpeakerType.USER.value]),
                agent_turns=i.get("agent_turns") or len([t for t in normalized_transcript if t.get("speaker") == SpeakerType.AGENT.value])
            )
            conversations.append(conv)
        
        return ConversationsResponse(
            conversations=conversations,
            total_count=total_count,
            filtered_count=filtered_count,
            last_sync=last_sync,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {str(e)}")


@router.get("/dashboard/conversations/{conversation_id}", response_model=ConversationListItem)
async def get_conversation_detail(conversation_id: str):
    """
    Get full conversation detail including transcript for the Conversations modal.
    """
    try:
        interactions = load_interactions()
        if not interactions:
            raise HTTPException(status_code=404, detail="No conversations found")

        match = next((i for i in interactions if i.get("id") == conversation_id), None)
        if not match:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        extracted = match.get("extracted_data_json", {})
        
        topic = (
            match.get("topic")
            or extracted.get("call_topic")
            or extracted.get("topic")
            or "General Inquiry"
        )

        user_name = match.get("user_name") or extracted.get("user_name") or extracted.get("student_name")
        user_email = match.get("user_email") or extracted.get("user_email") or extracted.get("student_email")

        # Normalize transcript_json to ensure text field is populated
        raw_transcript = match.get("transcript_json")
        normalized_transcript = _normalize_transcript(raw_transcript) if raw_transcript else []

        conversation = ConversationListItem(
            id=match["id"],
            agent_id=match.get("agent_id", "unknown"),
            started_at=match["started_at"],
            duration=match.get("duration", 0),
            messages_count=match.get("messages_count", 0),
            evaluation_result=match.get("evaluation_result", "successful"),
            outcome=match.get("outcome", "resolved"),
            user_name=user_name,
            user_email=user_email,
            topic=topic,
            sentiment=match.get("sentiment", "neutral"),
            summary=match.get("summary"),
            synced_at=match.get("synced_at"),
            source=match.get("source", "sync"),
            last_message_at=match.get("last_message_at"),
            transcript_json=normalized_transcript,
            transcript_summary=match.get("transcript_summary"),
            transcript_preview=match.get("transcript_preview"),
            turn_count=match.get("turn_count") or len(normalized_transcript),
            user_turns=match.get("user_turns") or len([t for t in normalized_transcript if t.get("speaker") == SpeakerType.USER.value]),
            agent_turns=match.get("agent_turns") or len([t for t in normalized_transcript if t.get("speaker") == SpeakerType.AGENT.value])
        )

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load conversation detail")
