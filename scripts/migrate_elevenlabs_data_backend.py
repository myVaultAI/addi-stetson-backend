#!/usr/bin/env python3
"""
ElevenLabs Historical Data Migration Script - Backend Integration

This script pulls all conversation data from ElevenLabs and sends it
to the running backend via API calls to populate the database.
"""

import asyncio
import sys
import os
import logging
import httpx
import hmac
import hashlib
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

# Backend API configuration
BACKEND_URL = "http://localhost:44000"

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

async def send_interaction_to_backend(interaction_data: Dict[str, Any]) -> bool:
    """Send interaction data to the running backend with HMAC signature"""
    try:
        # Create HMAC signature
        webhook_secret = os.getenv('ELEVENLABS_WEBHOOK_SECRET')
        if not webhook_secret:
            logger.warning("ELEVENLABS_WEBHOOK_SECRET not set - sending without signature")
            headers = {"Content-Type": "application/json"}
            body_data = json.dumps(interaction_data)
        else:
            # Create signature using raw body bytes (matching backend verification)
            body_data = json.dumps(interaction_data)
            signature = hmac.new(
                webhook_secret.encode('utf-8'),
                body_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                "Content-Type": "application/json",
                "ElevenLabs-Signature": signature
            }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/webhooks/interaction/log",
                content=body_data,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Successfully sent interaction {interaction_data['data']['conversation_id']} to backend")
            return True
    except Exception as e:
        logger.error(f"Failed to send interaction to backend: {str(e)}")
        return False

async def send_escalation_to_backend(escalation_data: Dict[str, Any]) -> bool:
    """Send escalation data to the running backend"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/webhooks/escalation/create",
                json=escalation_data
            )
            response.raise_for_status()
            logger.info(f"Successfully sent escalation for {escalation_data['student_name']} to backend")
            return True
    except Exception as e:
        logger.error(f"Failed to send escalation to backend: {str(e)}")
        return False

async def clear_backend_data():
    """Clear all existing data from the backend"""
    try:
        # Delete the data files
        import os
        data_dir = "data"
        interactions_file = os.path.join(data_dir, "interactions.json")
        escalations_file = os.path.join(data_dir, "escalations.json")
        
        if os.path.exists(interactions_file):
            os.remove(interactions_file)
            logger.info("Cleared interactions.json")
        
        if os.path.exists(escalations_file):
            os.remove(escalations_file)
            logger.info("Cleared escalations.json")
            
        logger.info("Backend data cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear backend data: {str(e)}")
        return False

async def migrate_historical_data():
    """Pull all ElevenLabs data and send to running backend"""
    logger.info("Starting ElevenLabs historical data migration...")
    
    try:
        # Initialize API client
        client = ElevenLabsAPIClient()
        
        # Test connection first
        if not await client.test_connection():
            logger.error("Failed to connect to ElevenLabs API. Check your API key.")
            return False
        
        # Test backend connection
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.get(f"{BACKEND_URL}/health")
                response.raise_for_status()
                logger.info("Backend connection test successful")
        except Exception as e:
            logger.error(f"Backend connection test failed: {str(e)}")
            logger.error("Make sure the backend is running on port 44000")
            return False
        
        # Clear existing data first
        logger.info("Clearing existing data...")
        await clear_backend_data()
        
        # Get ALL conversations from ElevenLabs (no agent filter)
        logger.info("Fetching ALL conversations from ElevenLabs (no agent filter)")
        conversations = await client.get_all_conversations(agent_id=None)
        
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
                    transcript_entries.append({
                        "speaker": "agent" if entry.get("role") == "agent" else "user",
                        "text": entry.get("message", ""),
                        "timestamp": entry.get("time_in_call_secs", 0.0)
                    })
                
                # Create interaction data for backend
                interaction_data = {
                    "type": "post_call_transcription",
                    "data": {
                        "conversation_id": conv_id,
                        "agent_id": full_data.get("agent_id", "unknown"),
                        "transcript": transcript_entries,
                        "analysis": {
                            "transcript_summary": analysis.get("transcript_summary", ""),
                            "call_successful": analysis.get("call_successful", False),
                            "data_collection_result": collected_data
                        },
                        "metadata": {
                            "call_duration_secs": metadata.get("call_duration_secs", 0),
                            "start_time_unix_secs": metadata.get("start_time_unix_secs", int(datetime.now().timestamp())),
                            "phone_call": metadata.get("phone_call", {})
                        }
                    }
                }
                
                # Send to backend
                if await send_interaction_to_backend(interaction_data):
                    processed_count += 1
                
                # Check for escalations
                if is_escalation_conversation(collected_data):
                    logger.info(f"Found escalation data in conversation {conv_id}")
                    
                    student_info = extract_student_data(collected_data)
                    
                    # Create escalation data for backend
                    escalation_data = {
                        "student_name": student_info.get("student_name", "Unknown Student"),
                        "student_email": student_info.get("student_email", ""),
                        "student_phone": student_info.get("student_phone", ""),
                        "inquiry_topic": student_info.get("inquiry_topic", "General Inquiry"),
                        "best_time_to_call": student_info.get("best_time_to_call", ""),
                        "conversation_id": conv_id
                    }
                    
                    # Send to backend
                    if await send_escalation_to_backend(escalation_data):
                        escalation_count += 1
                        logger.info(f"Created escalation for {escalation_data['student_name']} ({escalation_data['student_email']})")
                
            except Exception as e:
                logger.error(f"Error processing conversation {conv_id}: {str(e)}")
                continue
        
        logger.info(f"Migration complete!")
        logger.info(f"✅ Processed {processed_count} interactions")
        logger.info(f"✅ Created {escalation_count} escalations")
        logger.info(f"Check your dashboard at http://localhost:41001 to see the data")
        
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
