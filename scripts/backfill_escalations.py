#!/usr/bin/env python3
"""
Backfill escalations from existing conversations.

This script scans all conversations in interactions.json and creates escalation
records for conversations where:
1. Tool calls include 'escalate_to_human'
2. Transcript contains appointment/admissions/human request keywords
3. Extracted data shows appointment requests

Created: November 16, 2025
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions.json")
ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")

# Escalation indicators
ESCALATION_KEYWORDS = [
    'appointment', 'schedule', 'meeting', 'speak to', 'talk to', 'human',
    'admissions', 'counselor', 'representative', 'rep', 'financial aid',
    'contact me', 'call me', 'reach out', 'follow up', 'get in touch'
]

def load_interactions() -> List[Dict[str, Any]]:
    """Load conversations from interactions.json"""
    if not os.path.exists(INTERACTIONS_FILE):
        logger.warning(f"Interactions file not found: {INTERACTIONS_FILE}")
        return []
    
    try:
        with open(INTERACTIONS_FILE, 'r') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} conversations from {INTERACTIONS_FILE}")
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Failed to load interactions: {e}")
        return []

def load_existing_escalations() -> List[Dict[str, Any]]:
    """Load existing escalations to avoid duplicates"""
    if not os.path.exists(ESCALATIONS_FILE):
        return []
    
    try:
        with open(ESCALATIONS_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning(f"Failed to load existing escalations: {e}")
        return []

def save_escalations(escalations: List[Dict[str, Any]]) -> None:
    """Save escalations to file"""
    ensure_data_dir()
    try:
        with open(ESCALATIONS_FILE, 'w') as f:
            json.dump(escalations, f, indent=2, default=str)
        logger.info(f"Saved {len(escalations)} escalations to {ESCALATIONS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save escalations: {e}")
        raise

def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created data directory: {DATA_DIR}")

def has_escalation_tool_call(conversation: Dict[str, Any]) -> bool:
    """Check if conversation has escalate_to_human tool call"""
    transcript = conversation.get("transcript_json", [])
    
    for entry in transcript:
        tool_calls = entry.get("tool_calls", [])
        if tool_calls:
            for tool in tool_calls:
                if isinstance(tool, dict):
                    tool_name = tool.get("tool_name") or tool.get("name", "")
                    if "escalate" in tool_name.lower() or "escalation" in tool_name.lower():
                        return True
                elif isinstance(tool, str):
                    if "escalate" in tool.lower():
                        return True
    return False

def extract_tool_call_params(conversation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract escalation data from tool call parameters"""
    transcript = conversation.get("transcript_json", [])
    
    for entry in transcript:
        tool_calls = entry.get("tool_calls", [])
        if tool_calls:
            for tool in tool_calls:
                if isinstance(tool, dict):
                    tool_name = tool.get("tool_name") or tool.get("name", "")
                    if "escalate" in tool_name.lower():
                        # Try to extract params from tool
                        params = tool.get("params_as_json") or tool.get("params") or {}
                        
                        # If params_as_json is a string, parse it
                        if isinstance(params, str):
                            try:
                                params = json.loads(params)
                            except:
                                pass
                        
                        if isinstance(params, dict):
                            return {
                                "student_name": params.get("student_name") or params.get("studentName"),
                                "student_email": params.get("student_email") or params.get("studentEmail"),
                                "student_phone": params.get("student_phone") or params.get("studentPhone"),
                                "inquiry_topic": params.get("inquiry_topic") or params.get("inquiryTopic"),
                                "best_time_to_call": params.get("best_time_to_call") or params.get("bestTimeToCall")
                            }
        
        # Also check tool_results for escalation data
        tool_results = entry.get("tool_results", [])
        if tool_results:
            for result in tool_results:
                if isinstance(result, dict):
                    result_value = result.get("result_value")
                    if result_value and isinstance(result_value, str):
                        try:
                            result_data = json.loads(result_value)
                            if "escalation_id" in result_data:
                                # This is from an escalation tool
                                return {
                                    "student_name": conversation.get("user_name"),
                                    "student_email": conversation.get("user_email"),
                                    "inquiry_topic": conversation.get("topic", "General Inquiry")
                                }
                        except:
                            pass
    
    return None

def has_escalation_keywords(conversation: Dict[str, Any]) -> bool:
    """Check if conversation transcript contains escalation keywords"""
    transcript = conversation.get("transcript_json", [])
    summary = conversation.get("summary", "") or conversation.get("transcript_summary", "")
    
    # Check summary
    summary_lower = summary.lower()
    for keyword in ESCALATION_KEYWORDS:
        if keyword in summary_lower:
            return True
    
    # Check transcript entries
    for entry in transcript:
        text = entry.get("text") or entry.get("original_message") or ""
        text_lower = text.lower()
        for keyword in ESCALATION_KEYWORDS:
            if keyword in text_lower:
                return True
    
    return False

def extract_from_transcript(conversation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract student data from transcript text and summary"""
    transcript = conversation.get("transcript_json", [])
    summary = conversation.get("summary", "") or conversation.get("transcript_summary", "") or ""
    
    extracted = {
        "student_name": conversation.get("user_name"),
        "student_email": conversation.get("user_email"),
        "student_phone": None,
        "inquiry_topic": conversation.get("topic", "General Inquiry"),
        "best_time_to_call": None
    }
    
    # Combine transcript and summary for extraction
    transcript_text = " ".join([
        entry.get("text", "") or entry.get("original_message", "") 
        for entry in transcript
    ])
    full_text = (summary + " " + transcript_text).lower()
    
    # Look for email patterns - check both summary and transcript
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # Check summary first (often has structured data like "email (xxx@yyy.com)")
    all_text = summary + " " + transcript_text
    emails = re.findall(email_pattern, all_text, re.IGNORECASE)
    if emails and not extracted["student_email"]:
        # Prefer emails in summary (more likely to be the collected one)
        summary_emails = re.findall(email_pattern, summary, re.IGNORECASE)
        extracted["student_email"] = summary_emails[0] if summary_emails else emails[0]
    
    # Look for phone patterns (multiple formats)
    phone_patterns = [
        r'(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})',  # 407-252-2589
        r'\((\d{3})\)\s?(\d{3})[-.\s]?(\d{4})',  # (407) 252-2589
        r'(\d{10})',  # 4072522589
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, transcript_text + " " + summary)
        if phones:
            phone = "".join(phones[0]) if isinstance(phones[0], tuple) else str(phones[0])
            extracted["student_phone"] = phone[:10] if len(phone) >= 10 else phone
            break
    
    # Try to extract name from summary/transcript (look for patterns like "name is X" or "X Torres")
    # Common patterns: "name is [Name]", "I'm [Name]", "This is [Name]"
    name_patterns = [
        r'(?:name is|i\'?m|this is|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "name is Jason Torres"
        r'([A-Z][a-z]+\s+Torres)',  # "Jason Torres"
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # Any two capitalized words
    ]
    for pattern in name_patterns:
        names = re.findall(pattern, transcript_text + " " + summary, re.IGNORECASE)
        if names and not extracted["student_name"]:
            # Filter out common false positives
            false_positives = [
                "Stetson University", "Financial Aid", "Admissions Counselor",
                "How Can", "Can I", "Can You", "I Am", "This Is",
                "Would You", "Could You", "May I", "Addi", "Hello"
            ]
            name = names[0].strip()
            name_lower = name.lower()
            # Skip if it's a common greeting or question phrase
            if (name not in false_positives and 
                not any(fp.lower() in name_lower for fp in false_positives) and
                len(name.split()) <= 3 and
                len(name.split()) >= 2 and  # Must be at least first + last name
                not name_lower.startswith(('how ', 'can ', 'would ', 'could ', 'may '))):
                extracted["student_name"] = name.title()
                break
    
    # Extract best time to call
    time_patterns = [
        r'(?:best time|preferred time|prefer|afternoon|morning|evening)',
    ]
    for pattern in time_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            if "afternoon" in full_text:
                extracted["best_time_to_call"] = "afternoon"
            elif "morning" in full_text:
                extracted["best_time_to_call"] = "morning"
            elif "evening" in full_text:
                extracted["best_time_to_call"] = "evening"
            break
    
    # Determine topic from keywords
    if "financial aid" in full_text or "financial" in full_text:
        extracted["inquiry_topic"] = "Financial Aid"
    elif "admissions" in full_text and ("appointment" in full_text or "meet" in full_text or "speak" in full_text):
        extracted["inquiry_topic"] = "Admissions Appointment"
    elif "appointment" in full_text or "schedule" in full_text:
        extracted["inquiry_topic"] = "Appointment Request"
    elif "admissions" in full_text:
        extracted["inquiry_topic"] = "Admissions Inquiry"
    
    # Return if we have at least name or email
    if extracted["student_name"] or extracted["student_email"]:
        return extracted
    
    return None

def should_create_escalation(conversation: Dict[str, Any]) -> bool:
    """Determine if conversation should create an escalation"""
    # Priority 1: Has escalation tool call
    if has_escalation_tool_call(conversation):
        return True
    
    # Priority 2: Has escalation keywords AND student data
    if has_escalation_keywords(conversation):
        # Check if we have at least name or email
        if conversation.get("user_name") or conversation.get("user_email"):
            return True
        # Or try to extract from transcript
        extracted = extract_from_transcript(conversation)
        if extracted and (extracted.get("student_name") or extracted.get("student_email")):
            return True
    
    return False

def create_escalation_from_conversation(conversation: Dict[str, Any], existing_ids: set) -> Optional[Dict[str, Any]]:
    """Create escalation record from conversation"""
    conv_id = conversation.get("id")
    if not conv_id:
        return None
    
    # Check if escalation already exists for this conversation
    if conv_id in existing_ids:
        logger.debug(f"Escalation already exists for conversation {conv_id}")
        return None
    
    # Try to extract data from tool calls first
    escalation_data = extract_tool_call_params(conversation)
    
    # Fall back to transcript extraction
    if not escalation_data:
        escalation_data = extract_from_transcript(conversation)
    
    # Fall back to conversation metadata
    if not escalation_data:
        escalation_data = {
            "student_name": conversation.get("user_name"),
            "student_email": conversation.get("user_email"),
            "inquiry_topic": conversation.get("topic", "General Inquiry")
        }
    
    # Validate we have at least name or email
    if not escalation_data or (not escalation_data.get("student_name") and not escalation_data.get("student_email")):
        logger.debug(f"Skipping conversation {conv_id} - no student data found")
        return None
    
    # Get conversation start time for created_at
    started_at = conversation.get("started_at")
    if isinstance(started_at, str):
        try:
            # Handle various datetime formats
            if 'T' in started_at:
                created_at = datetime.fromisoformat(started_at.replace('Z', '+00:00').replace('+00:00', ''))
            else:
                # Try parsing as simple date string "2025-10-26 11:02:02"
                created_at = datetime.strptime(started_at, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.debug(f"Failed to parse started_at '{started_at}': {e}")
            created_at = datetime.utcnow()
    elif isinstance(started_at, datetime):
        created_at = started_at
    else:
        created_at = datetime.utcnow()
    
    # Ensure UTC timezone
    if created_at.tzinfo is None:
        from datetime import timezone
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    # Generate escalation ID
    timestamp_str = created_at.strftime('%Y%m%d_%H%M%S')
    escalation_id = f"ESC_{timestamp_str}_{len(existing_ids) + 1}"
    
    escalation = {
        "id": escalation_id,
        "student_name": escalation_data.get("student_name", "Unknown"),
        "student_email": escalation_data.get("student_email") or None,  # Use None instead of empty string
        "student_phone": escalation_data.get("student_phone") or None,
        "inquiry_topic": escalation_data.get("inquiry_topic", "General Inquiry"),
        "best_time_to_call": escalation_data.get("best_time_to_call") or None,
        "conversation_id": conv_id,
        "created_at": created_at.isoformat(),
        "status": "pending",
        "assigned_to": None
    }
    
    # Validate we have at least name or email (double check)
    if not escalation["student_name"] or escalation["student_name"] == "Unknown":
        if not escalation["student_email"]:
            logger.debug(f"Skipping escalation for {conv_id} - no valid student name or email")
            return None
    
    return escalation

def main():
    """Main backfill function"""
    logger.info("=" * 60)
    logger.info("Escalation Backfill Script")
    logger.info("=" * 60)
    
    # Load conversations
    conversations = load_interactions()
    if not conversations:
        logger.error("No conversations found to process")
        return
    
    # Load existing escalations to avoid duplicates
    existing_escalations = load_existing_escalations()
    existing_ids = {esc.get("conversation_id") for esc in existing_escalations if esc.get("conversation_id")}
    logger.info(f"Found {len(existing_escalations)} existing escalations")
    
    # Process conversations
    new_escalations = []
    skipped = 0
    
    for conv in conversations:
        conv_id = conv.get("id", "unknown")
        
        if should_create_escalation(conv):
            escalation = create_escalation_from_conversation(conv, existing_ids)
            if escalation:
                new_escalations.append(escalation)
                existing_ids.add(conv_id)
                logger.info(f"Created escalation for {escalation['student_name']} ({escalation['student_email']}) - {conv_id}")
            else:
                skipped += 1
        else:
            skipped += 1
    
    # Merge with existing escalations
    all_escalations = existing_escalations + new_escalations
    
    # Save
    if new_escalations:
        save_escalations(all_escalations)
        logger.info("=" * 60)
        logger.info(f"✅ Successfully created {len(new_escalations)} new escalations")
        logger.info(f"✅ Total escalations: {len(all_escalations)}")
        logger.info(f"⏭️  Skipped {skipped} conversations")
        logger.info("=" * 60)
    else:
        logger.info("=" * 60)
        logger.info(f"ℹ️  No new escalations created")
        logger.info(f"ℹ️  Total escalations: {len(existing_escalations)}")
        logger.info(f"⏭️  Skipped {skipped} conversations")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()

