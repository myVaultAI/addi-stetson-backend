#!/usr/bin/env python3
"""
Backfill script to enrich existing conversations with new metadata fields.
Run this after deploying the enhanced normalization function.

Usage:
    cd addi_backend
    python3 scripts/backfill_conversation_metadata.py
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path so we can import from routers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.webhooks import load_interactions, save_interactions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_outcome(raw: str) -> str:
    """Normalize outcome string to standard format"""
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


def backfill_metadata():
    """Backfill conversation metadata for existing records"""
    logger.info("=" * 60)
    logger.info("BACKFILL CONVERSATION METADATA")
    logger.info("=" * 60)
    
    # Load current interactions
    interactions = load_interactions()
    logger.info(f"Loaded {len(interactions)} interactions")
    
    if not interactions:
        logger.warning("No interactions found to backfill")
        return
    
    updated_count = 0
    skipped_count = 0
    
    for idx, interaction in enumerate(interactions):
        needs_update = False
        
        # Add messages_count if missing
        if "messages_count" not in interaction:
            transcript = interaction.get("transcript_json", [])
            interaction["messages_count"] = len(transcript) if transcript else 0
            needs_update = True
            logger.debug(f"  [{idx+1}] Added messages_count: {interaction['messages_count']}")
        
        # Add evaluation_result if missing
        if "evaluation_result" not in interaction:
            # Default to "successful" for completed calls
            outcome = interaction.get("outcome", "resolved")
            # Normalize outcome first
            normalized_outcome = normalize_outcome(outcome)
            
            if normalized_outcome == "resolved":
                interaction["evaluation_result"] = "successful"
            elif normalized_outcome == "failed":
                interaction["evaluation_result"] = "failed"
            else:
                interaction["evaluation_result"] = "needs_review"
            needs_update = True
            logger.debug(f"  [{idx+1}] Added evaluation_result: {interaction['evaluation_result']}")
        
        # Add last_message_at if missing
        if "last_message_at" not in interaction:
            transcript = interaction.get("transcript_json", [])
            started_at = interaction.get("started_at")
            
            # Handle started_at being a string or datetime
            if isinstance(started_at, str):
                try:
                    started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                except:
                    started_at = datetime.utcnow()
            elif not isinstance(started_at, datetime):
                started_at = datetime.utcnow()
            
            if transcript and len(transcript) > 0:
                try:
                    last_entry = transcript[-1]
                    if isinstance(last_entry, dict):
                        last_ts = last_entry.get("timestamp", 0)
                        interaction["last_message_at"] = started_at + timedelta(seconds=last_ts)
                    else:
                        interaction["last_message_at"] = started_at
                    needs_update = True
                    logger.debug(f"  [{idx+1}] Added last_message_at from transcript")
                except Exception as e:
                    interaction["last_message_at"] = started_at
                    needs_update = True
                    logger.debug(f"  [{idx+1}] Added last_message_at (defaulted to started_at): {e}")
            else:
                interaction["last_message_at"] = started_at
                needs_update = True
                logger.debug(f"  [{idx+1}] Added last_message_at (defaulted to started_at - no transcript)")
        
        # Add user_name if missing (extract from extracted_data_json)
        if "user_name" not in interaction or interaction.get("user_name") is None:
            extracted = interaction.get("extracted_data_json", {})
            user_name = (
                extracted.get("user_name") or 
                extracted.get("student_name") or 
                None
            )
            if user_name:
                interaction["user_name"] = user_name
                needs_update = True
                logger.debug(f"  [{idx+1}] Added user_name: {user_name}")
        
        # Add user_email if missing (extract from extracted_data_json)
        if "user_email" not in interaction or interaction.get("user_email") is None:
            extracted = interaction.get("extracted_data_json", {})
            user_email = (
                extracted.get("user_email") or 
                extracted.get("student_email") or 
                None
            )
            if user_email:
                interaction["user_email"] = user_email
                needs_update = True
                logger.debug(f"  [{idx+1}] Added user_email: {user_email}")
        
        # Add topic if missing (extract from extracted_data_json)
        if "topic" not in interaction or interaction.get("topic") == "General Inquiry":
            extracted = interaction.get("extracted_data_json", {})
            topic = (
                extracted.get("call_topic") or 
                extracted.get("topic") or 
                "General Inquiry"
            )
            interaction["topic"] = topic
            needs_update = True
            logger.debug(f"  [{idx+1}] Added/updated topic: {topic}")
        
        # Add synced_at if missing (for tracking when data was synced)
        if "synced_at" not in interaction:
            # Use created_at or current time as fallback
            created_at = interaction.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.utcnow()
            elif not isinstance(created_at, datetime):
                created_at = datetime.utcnow()
            
            interaction["synced_at"] = created_at
            needs_update = True
            logger.debug(f"  [{idx+1}] Added synced_at: {interaction['synced_at']}")
        
        # Ensure outcome is normalized
        current_outcome = interaction.get("outcome", "resolved")
        normalized_outcome = normalize_outcome(current_outcome)
        if current_outcome != normalized_outcome:
            interaction["outcome"] = normalized_outcome
            needs_update = True
            logger.debug(f"  [{idx+1}] Normalized outcome: {current_outcome} -> {normalized_outcome}")
        
        # Update interaction in list
        if needs_update:
            interactions[idx] = interaction
            updated_count += 1
        else:
            skipped_count += 1
    
    # Save updated interactions
    if updated_count > 0:
        logger.info("=" * 60)
        logger.info(f"Saving {len(interactions)} interactions (updated {updated_count}, skipped {skipped_count})")
        save_interactions(interactions)
        logger.info("✅ Backfill complete!")
    else:
        logger.info("=" * 60)
        logger.info(f"No updates needed ({skipped_count} interactions already have all fields)")
    
    logger.info("=" * 60)
    logger.info(f"Summary:")
    logger.info(f"  - Total interactions: {len(interactions)}")
    logger.info(f"  - Updated: {updated_count}")
    logger.info(f"  - Skipped: {skipped_count}")
    logger.info("=" * 60)
    
    return {
        "total": len(interactions),
        "updated": updated_count,
        "skipped": skipped_count
    }


if __name__ == "__main__":
    try:
        result = backfill_metadata()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backfill failed: {str(e)}", exc_info=True)
        sys.exit(1)

