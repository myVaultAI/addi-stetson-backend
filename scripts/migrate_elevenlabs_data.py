#!/usr/bin/env python3
"""
ElevenLabs Historical Data Migration Script

This script pulls all conversation data from ElevenLabs and populates
our local database with historical conversations and escalations.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.elevenlabs_api_client import ElevenLabsAPIClient
from models.calls import InteractionLog, EscalationSummary, TranscriptEntry, SpeakerType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our in-memory databases (these are defined in webhooks.py)
# We'll need to import them or recreate them here
interactions_db = []
escalations_db = []

def extract_student_data(collected_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract student information from collected data"""
    student_info = {}
    
    # Map common field names
    field_mapping = {
        'student_name': ['student_name', 'name', 'full_name', 'student_name'],
        'student_email': ['student_email', 'email', 'email_address'],
        'student_phone': ['student_phone', 'phone', 'phone_number', 'contact_number'],
        'inquiry_topic': ['inquiry_topic', 'topic', 'subject', 'program_interest'],
        'best_time_to_call': ['best_time_to_call', 'preferred_time', 'call_time']
    }
    
    for target_field, possible_keys in field_mapping.items():
        for key in possible_keys:
            if key in collected_data:
                value = collected_data[key]
                # Handle both direct values and nested objects
                if isinstance(value, dict) and 'value' in value:
                    student_info[target_field] = value['value']
                elif isinstance(value, str):
                    student_info[target_field] = value
                break
    
    return student_info

def is_escalation_conversation(collected_data: Dict[str, Any]) -> bool:
    """Determine if a conversation contains escalation data"""
    escalation_indicators = [
        'student_name', 'student_email', 'appointment_request', 
        'schedule_appointment', 'speak_to_human', 'transfer_request'
    ]
    
    for indicator in escalation_indicators:
        if indicator in collected_data:
            return True
    
    # Check for appointment-related keywords in any field
    for key, value in collected_data.items():
        if isinstance(value, dict) and 'value' in value:
            text_value = str(value['value']).lower()
            if any(keyword in text_value for keyword in ['appointment', 'schedule', 'meeting', 'call back']):
                return True
        elif isinstance(value, str):
            if any(keyword in value.lower() for keyword in ['appointment', 'schedule', 'meeting', 'call back']):
                return True
    
    return False

async def migrate_historical_data():
    """Pull all ElevenLabs data and populate our database"""
    logger.info("Starting ElevenLabs historical data migration...")
    
    try:
        # Initialize API client
        client = ElevenLabsAPIClient()
        
        # Test connection first
        if not await client.test_connection():
            logger.error("Failed to connect to ElevenLabs API. Check your API key.")
            return False
        
        # Your agent ID from ElevenLabs dashboard
        agent_id = "agent_0301k84pwdr2ffprwkqaha0f178g"  # Update this if needed
        
        logger.info(f"Fetching conversations for agent: {agent_id}")
        conversations = await client.get_all_conversations(agent_id)
        
        if not conversations:
            logger.warning("No conversations found for this agent")
            return True
        
        logger.info(f"Found {len(conversations)} conversations to process")
        
        processed_count = 0
        escalation_count = 0
        
        for conv_summary in conversations:
            conv_id = conv_summary["conversation_id"]
            logger.info(f"Processing conversation {processed_count + 1}/{len(conversations)}: {conv_id}")
            
            try:
                # Get full details
                full_data = await client.get_conversation_details(conv_id)
                
                # Extract conversation data
                metadata = full_data.get("metadata", {})
                analysis = full_data.get("analysis", {})
                collected_data = analysis.get("data_collection_result", {})
                
                # Convert transcript to our format
                transcript_entries = []
                for entry in full_data.get("transcript", []):
                    speaker = SpeakerType.AGENT if entry.get("role") == "agent" else SpeakerType.USER
                    transcript_entries.append(TranscriptEntry(
                        speaker=speaker,
                        text=entry.get("message", ""),
                        timestamp=entry.get("time_in_call_secs", 0.0)
                    ))
                
                # Create interaction log
                interaction_log = InteractionLog(
                    conversation_id=conv_id,
                    agent_id=full_data.get("agent_id", agent_id),
                    timestamp=datetime.fromtimestamp(
                        metadata.get("start_time_unix_secs", datetime.now().timestamp())
                    ),
                    duration_seconds=metadata.get("call_duration_secs", 0),
                    transcript=transcript_entries,
                    summary=analysis.get("transcript_summary", ""),
                    extracted_data=collected_data,
                    call_outcome=None  # We'll determine this based on collected data
                )
                
                # Save to database
                interactions_db.append(interaction_log.__dict__)
                processed_count += 1
                
                # Check for escalations
                if is_escalation_conversation(collected_data):
                    logger.info(f"Found escalation data in conversation {conv_id}")
                    
                    student_info = extract_student_data(collected_data)
                    
                    # Create escalation
                    escalation = EscalationSummary(
                        id=f"esc_{conv_id}",
                        student_name=student_info.get("student_name", "Unknown Student"),
                        student_email=student_info.get("student_email", ""),
                        student_phone=student_info.get("student_phone", ""),
                        inquiry_topic=student_info.get("inquiry_topic", "General Inquiry"),
                        best_time_to_call=student_info.get("best_time_to_call", ""),
                        conversation_id=conv_id,
                        created_at=interaction_log.timestamp,
                        status="pending",
                        assigned_to=None,
                        priority="medium"
                    )
                    
                    escalations_db.append(escalation.__dict__)
                    escalation_count += 1
                    
                    logger.info(f"Created escalation for {escalation.student_name} ({escalation.student_email})")
                
            except Exception as e:
                logger.error(f"Error processing conversation {conv_id}: {str(e)}")
                continue
        
        logger.info(f"Migration complete!")
        logger.info(f"✅ Processed {processed_count} conversations")
        logger.info(f"✅ Created {escalation_count} escalations")
        logger.info(f"✅ Total interactions in database: {len(interactions_db)}")
        logger.info(f"✅ Total escalations in database: {len(escalations_db)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("ELEVENLABS HISTORICAL DATA MIGRATION")
    logger.info("=" * 60)
    
    # Check for API key
    if not os.getenv("ELEVENLABS_API_KEY"):
        logger.error("ELEVENLABS_API_KEY environment variable not set!")
        logger.error("Please set it in your .env file or environment")
        return
    
    success = await migrate_historical_data()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        logger.info("Check your dashboard at http://localhost:41001 to see the data")
    else:
        logger.error("❌ Migration failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())
