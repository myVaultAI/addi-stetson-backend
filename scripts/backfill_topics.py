#!/usr/bin/env python3
"""
Backfill script to extract topics from conversation transcripts.
Identifies Marine Biology, Admissions, Financial Aid, and other topics.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

INTERACTIONS_FILE = Path(__file__).parent.parent / "data" / "interactions.json"


def load_interactions() -> List[Dict[str, Any]]:
    """Load interactions from JSON file."""
    if not INTERACTIONS_FILE.exists():
        print(f"❌ File not found: {INTERACTIONS_FILE}")
        return []
    
    with open(INTERACTIONS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_interactions(interactions: List[Dict[str, Any]]) -> None:
    """Save interactions back to JSON file."""
    with open(INTERACTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(interactions, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(interactions)} interactions to {INTERACTIONS_FILE}")


def get_full_transcript_text(interaction: Dict[str, Any]) -> str:
    """Extract full transcript text from interaction."""
    transcript_json = interaction.get("transcript_json", [])
    if not transcript_json or not isinstance(transcript_json, list):
        return ""
    
    lines = []
    for turn in transcript_json:
        text = turn.get("text") or turn.get("original_message") or turn.get("message") or ""
        if text:
            lines.append(text.lower())
    
    summary = interaction.get("summary") or interaction.get("transcript_summary") or ""
    return f"{' '.join(lines)} {summary.lower()}"


def extract_topic(interaction: Dict[str, Any]) -> str:
    """Extract topic from conversation content."""
    text = get_full_transcript_text(interaction)
    
    # Priority-based topic extraction
    topic_keywords = {
        "Admissions Appointment": [
            "appointment", "admissions counselor", "meet with", "schedule", 
            "admissions rep", "visit", "talk to someone"
        ],
        "Financial Aid": [
            "financial aid", "scholarship", "cost", "tuition", "afford",
            "financial assistance", "money", "pay for", "expenses"
        ],
        "Marine Biology": [
            "marine biology", "marine science", "ocean", "sea", "aquatic",
            "oceanography", "marine lab", "marine research"
        ],
        "Campus Tour": [
            "campus tour", "visit campus", "see the campus", "tour"
        ],
        "Application Process": [
            "apply", "application", "requirements", "admission requirements",
            "how to get in", "acceptance"
        ],
        "Programs & Academics": [
            "major", "program", "degree", "course", "study", "academic"
        ]
    }
    
    # Check each topic in priority order
    for topic, keywords in topic_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return topic
    
    # Default fallback
    return "General Inquiry"


def main():
    """Main backfill script."""
    print("🔄 Starting topic extraction backfill...")
    print(f"📁 Loading interactions from: {INTERACTIONS_FILE}")
    
    interactions = load_interactions()
    if not interactions:
        print("❌ No interactions found")
        return
    
    print(f"✅ Loaded {len(interactions)} interactions")
    print()
    
    updated_count = 0
    
    for interaction in interactions:
        conv_id = interaction.get("id", "unknown")
        current_topic = interaction.get("topic")
        
        # Extract topic from transcript
        extracted_topic = extract_topic(interaction)
        
        # Only update if topic changed
        if extracted_topic != current_topic:
            print(f"📝 Updating {conv_id[:20]}...")
            print(f"   Old: {current_topic}")
            print(f"   New: {extracted_topic}")
            print()
            
            interaction["topic"] = extracted_topic
            updated_count += 1
        
        # Also update in extracted_data_json if it exists
        if "extracted_data_json" in interaction and interaction["extracted_data_json"]:
            interaction["extracted_data_json"]["inquiry_topic"] = extracted_topic
    
    print()
    print("=" * 60)
    print(f"✅ Updated: {updated_count} conversations")
    print(f"⏭️  Skipped: {len(interactions) - updated_count} conversations (no change)")
    print(f"📊 Total:   {len(interactions)} conversations")
    print("=" * 60)
    
    # Show topic breakdown
    topic_counts = {}
    for interaction in interactions:
        topic = interaction.get("topic", "Unknown")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    print()
    print("📊 Topic Breakdown:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {topic}: {count}")
    
    if updated_count > 0:
        print()
        save_interactions(interactions)
        print()
        print("✅ Topic extraction complete!")
    else:
        print()
        print("ℹ️  No updates needed - all topics are current.")


if __name__ == "__main__":
    main()

