#!/usr/bin/env python3
"""
Direct ElevenLabs Data Migration - Write ONLY Real Data to Files

This script pulls the ACTUAL ElevenLabs data and writes it directly to the data files,
bypassing the backend API to avoid appending issues.
"""

import asyncio
import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.elevenlabs_api_client import ElevenLabsAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data file paths
DATA_DIR = "data"
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions.json")
ESCALATIONS_FILE = os.path.join(DATA_DIR, "escalations.json")

def ensure_data_dir():
    """Ensure data directory exists"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logger.info(f"Created data directory: {DATA_DIR}")

def write_interactions_directly(interactions):
    """Write interactions directly to file"""
    ensure_data_dir()
    try:
        with open(INTERACTIONS_FILE, 'w') as f:
            json.dump(interactions, f, indent=2, default=str)
        logger.info(f"Wrote {len(interactions)} interactions directly to file")
    except Exception as e:
        logger.error(f"Failed to write interactions: {e}")

def write_escalations_directly(escalations):
    """Write escalations directly to file"""
    ensure_data_dir()
    try:
        with open(ESCALATIONS_FILE, 'w') as f:
            json.dump(escalations, f, indent=2, default=str)
        logger.info(f"Wrote {len(escalations)} escalations directly to file")
    except Exception as e:
        logger.error(f"Failed to write escalations: {e}")

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
    
    for target_field, possible_fields in field_mapping.items():
        for field in possible_fields:
            if field in collected_data and collected_data[field]:
                student_info[target_field] = str(collected_data[field])
                break
    
    return student_info

def is_escalation_conversation(collected_data: Dict[str, Any]) -> bool:
    """Check if conversation contains escalation data"""
    escalation_indicators = [
        'student_name', 'student_email', 'student_phone',
        'inquiry_topic', 'appointment', 'schedule', 'counselor'
    ]
    
    for indicator in escalation_indicators:
        if indicator in collected_data and collected_data[indicator]:
            return True
    
    return False

async def migrate_direct_to_files():
    """Pull ElevenLabs data and write directly to files"""
    logger.info("Starting DIRECT ElevenLabs data migration...")
    
    try:
        # Initialize API client
        client = ElevenLabsAPIClient()
        
        # Test connection
        if not await client.test_connection():
            logger.error("ElevenLabs API connection failed")
            return False
        
        logger.info("✅ ElevenLabs API connection successful")
        
        # Get ALL conversations from ElevenLabs (no agent filter)
        logger.info("Fetching ALL conversations from ElevenLabs (no agent filter)")
        conversations = await client.get_all_conversations(agent_id=None)
        
        if not conversations:
            logger.warning("No conversations found")
            return True
        
        logger.info(f"Found {len(conversations)} conversations to process")
        
        interactions = []
        escalations = []
        
        for conv_summary in conversations:
            conv_id = conv_summary["conversation_id"]
            logger.info(f"Processing conversation: {conv_id}")
            
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
                    transcript_entries.append({
                        "speaker": "agent" if entry.get("role") == "agent" else "user",
                        "text": entry.get("message", ""),
                        "timestamp": entry.get("time_in_call_secs", 0.0)
                    })
                
                # Create interaction data
                interaction = {
                    "id": conv_id,
                    "agent_id": full_data.get("agent_id", "unknown"),
                    "started_at": datetime.fromtimestamp(
                        metadata.get("start_time_unix_secs", datetime.now().timestamp())
                    ),
                    "duration": metadata.get("call_duration_secs", 0),
                    "transcript_json": transcript_entries,
                    "summary": analysis.get("transcript_summary", ""),
                    "extracted_data": collected_data,
                    "call_outcome": "successful" if analysis.get("call_successful", False) else "failed",
                    "created_at": datetime.fromtimestamp(
                        metadata.get("start_time_unix_secs", datetime.now().timestamp())
                    )
                }
                
                interactions.append(interaction)
                
                # Check for escalations
                if is_escalation_conversation(collected_data):
                    logger.info(f"Found escalation data in conversation {conv_id}")
                    
                    student_info = extract_student_data(collected_data)
                    
                    # Create escalation data
                    escalation = {
                        "id": f"ESC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(escalations) + 1}",
                        "student_name": student_info.get("student_name", "Unknown Student"),
                        "student_email": student_info.get("student_email", ""),
                        "student_phone": student_info.get("student_phone", ""),
                        "inquiry_topic": student_info.get("inquiry_topic", "General Inquiry"),
                        "best_time_to_call": student_info.get("best_time_to_call", ""),
                        "conversation_id": conv_id,
                        "created_at": datetime.fromtimestamp(
                            metadata.get("start_time_unix_secs", datetime.now().timestamp())
                        ),
                        "status": "pending",
                        "assigned_to": None
                    }
                    
                    escalations.append(escalation)
                    logger.info(f"Created escalation for {escalation['student_name']} ({escalation['student_email']})")
                
            except Exception as e:
                logger.error(f"Error processing conversation {conv_id}: {str(e)}")
                continue
        
        # Write data directly to files
        write_interactions_directly(interactions)
        write_escalations_directly(escalations)
        
        logger.info(f"Migration complete!")
        logger.info(f"✅ Processed {len(interactions)} interactions")
        logger.info(f"✅ Created {len(escalations)} escalations")
        logger.info(f"Check your dashboard at http://localhost:41001 to see the data")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

async def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("DIRECT ELEVENLABS DATA MIGRATION")
    logger.info("=" * 60)
    
    # Check for API key
    if not os.getenv("ELEVENLABS_API_KEY"):
        logger.error("ELEVENLABS_API_KEY environment variable not set!")
        logger.error("Please set it in your .env file or environment")
        return
    
    success = await migrate_direct_to_files()
    
    if success:
        logger.info("🎉 Migration completed successfully!")
        logger.info("Check your dashboard at http://localhost:41001 to see the data")
    else:
        logger.error("❌ Migration failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())
