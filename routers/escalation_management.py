"""
Escalation Management Endpoints
Handles status updates, notes, and escalation lifecycle management
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import os
import json
import logging
from datetime import datetime, timezone
import uuid

from models.calls import (
    EscalationSummary,
    EscalationStatusUpdate,
    EscalationNoteCreate,
    EscalationNote
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/webhooks/escalations", tags=["escalation-management"])

# File-based persistence
DATA_DIR = "data"
ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")


def load_escalations() -> List[dict]:
    """Load escalations from JSON file"""
    try:
        if os.path.exists(ESCALATIONS_FILE):
            with open(ESCALATIONS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Failed to load escalations: {str(e)}")
        return []


def save_escalations(escalations: List[dict]) -> None:
    """Save escalations to JSON file"""
    try:
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with open(ESCALATIONS_FILE, 'w') as f:
            json.dump(escalations, f, indent=2, default=str)
        
        logger.info(f"Saved {len(escalations)} escalations")
    except Exception as e:
        logger.error(f"Failed to save escalations: {str(e)}")
        raise


@router.patch("/{escalation_id}/status")
async def update_escalation_status(
    escalation_id: str,
    update: EscalationStatusUpdate
):
    """
    Update the status of an escalation.
    Valid statuses: pending, contacted, resolved
    """
    try:
        escalations = load_escalations()
        
        # Find the escalation
        escalation = next((esc for esc in escalations if esc["id"] == escalation_id), None)
        if not escalation:
            raise HTTPException(status_code=404, detail=f"Escalation {escalation_id} not found")
        
        # Validate status
        valid_statuses = ["pending", "contacted", "resolved"]
        if update.status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update escalation
        old_status = escalation["status"]
        escalation["status"] = update.status
        escalation["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        if update.assigned_to:
            escalation["assigned_to"] = update.assigned_to
        
        # Add note if provided
        if update.note:
            if "notes" not in escalation:
                escalation["notes"] = []
            
            note = {
                "id": f"NOTE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                "escalation_id": escalation_id,
                "author": "Dashboard User",
                "text": f"Status changed from {old_status} to {update.status}. {update.note}",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            escalation["notes"].append(note)
        
        # Save changes
        save_escalations(escalations)
        
        logger.info(f"Updated escalation {escalation_id} status from {old_status} to {update.status}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "old_status": old_status,
            "new_status": update.status,
            "updated_at": escalation["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update escalation status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update escalation: {str(e)}")


@router.post("/{escalation_id}/notes")
async def add_escalation_note(
    escalation_id: str,
    note_data: EscalationNoteCreate
):
    """Add a note/comment to an escalation"""
    try:
        escalations = load_escalations()
        
        # Find the escalation
        escalation = next((esc for esc in escalations if esc["id"] == escalation_id), None)
        if not escalation:
            raise HTTPException(status_code=404, detail=f"Escalation {escalation_id} not found")
        
        # Create note
        note = {
            "id": f"NOTE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
            "escalation_id": escalation_id,
            "author": note_data.author,
            "text": note_data.text,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add note to escalation
        if "notes" not in escalation:
            escalation["notes"] = []
        
        escalation["notes"].append(note)
        escalation["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save changes
        save_escalations(escalations)
        
        logger.info(f"Added note to escalation {escalation_id}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "note": note
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add note: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add note: {str(e)}")


@router.get("/{escalation_id}/notes", response_model=List[EscalationNote])
async def get_escalation_notes(escalation_id: str):
    """Get all notes for an escalation"""
    try:
        escalations = load_escalations()
        
        # Find the escalation
        escalation = next((esc for esc in escalations if esc["id"] == escalation_id), None)
        if not escalation:
            raise HTTPException(status_code=404, detail=f"Escalation {escalation_id} not found")
        
        # Get notes
        notes = escalation.get("notes", [])
        
        # Convert to response format
        note_objects = []
        for note in notes:
            note_obj = EscalationNote(
                id=note["id"],
                escalation_id=note["escalation_id"],
                author=note["author"],
                text=note["text"],
                created_at=datetime.fromisoformat(note["created_at"])
            )
            note_objects.append(note_obj)
        
        return note_objects
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notes: {str(e)}")


@router.get("/{escalation_id}", response_model=EscalationSummary)
async def get_escalation_detail(escalation_id: str):
    """Get full details of a single escalation including notes"""
    try:
        escalations = load_escalations()
        
        # Find the escalation
        escalation = next((esc for esc in escalations if esc["id"] == escalation_id), None)
        if not escalation:
            raise HTTPException(status_code=404, detail=f"Escalation {escalation_id} not found")
        
        # Calculate priority
        created_at = datetime.fromisoformat(escalation["created_at"].replace('Z', '+00:00'))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        age_hours = (now - created_at).total_seconds() / 3600
        
        if age_hours > 24:
            priority = "urgent"
        elif age_hours > 12:
            priority = "high"
        else:
            priority = "medium"
        
        # Convert notes to Note objects
        notes = []
        for note_data in escalation.get("notes", []):
            note = EscalationNote(
                id=note_data["id"],
                escalation_id=note_data["escalation_id"],
                author=note_data["author"],
                text=note_data["text"],
                created_at=datetime.fromisoformat(note_data["created_at"])
            )
            notes.append(note)
        
        # Create summary with notes
        updated_at = None
        if "updated_at" in escalation:
            updated_at = datetime.fromisoformat(escalation["updated_at"])
        
        summary = EscalationSummary(
            id=escalation["id"],
            student_name=escalation["student_name"],
            student_email=escalation.get("student_email"),
            student_phone=escalation.get("student_phone"),
            inquiry_topic=escalation["inquiry_topic"],
            best_time_to_call=escalation.get("best_time_to_call"),
            conversation_id=escalation.get("conversation_id"),
            created_at=created_at,
            updated_at=updated_at,
            status=escalation["status"],
            assigned_to=escalation.get("assigned_to"),
            priority=priority,
            notes=notes
        )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get escalation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get escalation: {str(e)}")

