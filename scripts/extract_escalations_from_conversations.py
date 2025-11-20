#!/usr/bin/env python3
"""
Extract escalations from conversations with escalate_to_human tool calls.
This script can be run manually to extract escalations from existing conversations.

Usage:
    python3 scripts/extract_escalations_from_conversations.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions from webhooks router
from routers.webhooks import (
    load_interactions,
    load_escalations,
    save_escalations,
    has_escalation_tool_call,
    extract_escalation_from_tool_call
)

def main():
    """Extract escalations from all conversations"""
    print("🔍 Loading conversations...")
    conversations = load_interactions()
    print(f"   Found {len(conversations)} conversations")
    
    print("\n🔍 Loading existing escalations...")
    existing_escalations = load_escalations()
    existing_conv_ids = {esc.get("conversation_id") for esc in existing_escalations if esc.get("conversation_id")}
    print(f"   Found {len(existing_escalations)} existing escalations")
    print(f"   Conversations with escalations: {len(existing_conv_ids)}")
    
    print("\n🔍 Checking for escalate_to_human tool calls...")
    escalations_created = 0
    
    for conv in conversations:
        conv_id = conv.get("id")
        
        # Skip if already has escalation
        if conv_id in existing_conv_ids:
            continue
        
        # Check if conversation has escalate_to_human tool call
        if has_escalation_tool_call(conv):
            print(f"\n   ✓ Found escalation in conversation {conv_id}")
            
            # Extract escalation data
            escalation_data = extract_escalation_from_tool_call(conv)
            
            if escalation_data and (escalation_data.get("student_name") or escalation_data.get("student_email")):
                # Generate escalation ID
                escalation_id = f"ESC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(existing_escalations) + escalations_created + 1}"
                escalation_data["id"] = escalation_id
                
                # Ensure created_at is timezone-aware
                if isinstance(escalation_data["created_at"], datetime):
                    if escalation_data["created_at"].tzinfo is None:
                        escalation_data["created_at"] = escalation_data["created_at"].replace(tzinfo=timezone.utc)
                elif isinstance(escalation_data["created_at"], str):
                    try:
                        dt = datetime.fromisoformat(escalation_data["created_at"].replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        escalation_data["created_at"] = dt
                    except:
                        escalation_data["created_at"] = datetime.now(timezone.utc)
                else:
                    escalation_data["created_at"] = datetime.now(timezone.utc)
                
                print(f"      Student: {escalation_data.get('student_name', 'N/A')}")
                print(f"      Email: {escalation_data.get('student_email', 'N/A')}")
                print(f"      Topic: {escalation_data.get('inquiry_topic', 'N/A')}")
                
                existing_escalations.append(escalation_data)
                escalations_created += 1
            else:
                print(f"      ⚠️  Could not extract escalation data")
    
    if escalations_created > 0:
        print(f"\n💾 Saving {escalations_created} new escalations...")
        save_escalations(existing_escalations)
        print(f"   ✅ Saved {len(existing_escalations)} total escalations")
    else:
        print("\n   ℹ️  No new escalations found")
    
    print(f"\n✅ Done! Created {escalations_created} new escalations")

if __name__ == "__main__":
    main()

