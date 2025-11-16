#!/usr/bin/env python3
"""
Backfill script to extract student names, emails, and phone numbers from conversation transcripts.
Similar to backfill_escalations.py but focused on extracting student contact information.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path to import from backend
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
        speaker = turn.get("speaker", "unknown")
        text = turn.get("text") or turn.get("original_message") or turn.get("message") or ""
        if text:
            lines.append(f"{speaker}: {text}")
    
    return "\n".join(lines)


def extract_name(text: str) -> Optional[str]:
    """Extract student name from text using regex patterns."""
    # Patterns for name extraction
    patterns = [
        r"(?:my name is|I'm|I am|this is|name's)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"(?:^|[\.\!\?]\s+)([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+and my email|,\s+and)",
        r"(?:It's|This is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            name = match.group(1).strip()
            
            # Filter out false positives
            false_positives = [
                "How Can", "Can I", "Stetson University", "Marine Biology",
                "Financial Aid", "Thank You", "Yes I", "No I", "Sure Sure",
                "Good Morning", "Good Afternoon", "Good Evening"
            ]
            
            if name and len(name) > 3 and not any(fp.lower() in name.lower() for fp in false_positives):
                # Validate it looks like a real name (2-4 words, each capitalized)
                words = name.split()
                if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                    return name
    
    return None


def extract_email(text: str) -> Optional[str]:
    """Extract email address from text using regex patterns."""
    # Pattern 1: Standard email format
    email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    match = re.search(email_pattern, text)
    if match:
        return match.group(1).lower()
    
    # Pattern 2: Spoken email format (e.g., "jasonwtorres at gmail dot com")
    spoken_pattern = r'([a-zA-Z0-9._%+-]+)\s+(?:at|@)\s+([a-zA-Z0-9.-]+)\s+(?:dot|\.)\s+([a-zA-Z]{2,})'
    match = re.search(spoken_pattern, text, re.IGNORECASE)
    if match:
        username = match.group(1).replace(' ', '')
        domain = match.group(2).replace(' ', '')
        tld = match.group(3).replace(' ', '')
        return f"{username}@{domain}.{tld}".lower()
    
    # Pattern 3: Email with spaces (e.g., "itsthor Torres, I-T-S Thor Torres at gmail.com")
    spaced_pattern = r'(?:it\'?s\s+)?([a-zA-Z0-9]+)\s+([a-zA-Z]+).*?at\s+([a-zA-Z0-9]+)\.([a-zA-Z]{2,})'
    match = re.search(spaced_pattern, text, re.IGNORECASE)
    if match:
        username = (match.group(1) + match.group(2)).replace(' ', '')
        domain = match.group(3).replace(' ', '')
        tld = match.group(4).replace(' ', '')
        return f"{username}@{domain}.{tld}".lower()
    
    return None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text using regex patterns."""
    # Pattern 1: Standard formats
    patterns = [
        r'\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b',  # 407-252-2589 or 4072522589
        r'\b(\(\d{3}\)\s*\d{3}[-.]?\d{4})\b',  # (407) 252-2589
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(1)
            # Normalize format
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 10:
                return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits[0] == '1':
                return f"{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    
    return None


def extract_best_time(text: str) -> Optional[str]:
    """Extract best time to contact from text."""
    text_lower = text.lower()
    
    if 'afternoon' in text_lower:
        return 'afternoon'
    elif 'morning' in text_lower:
        return 'morning'
    elif 'evening' in text_lower:
        return 'evening'
    elif 'anytime' in text_lower or 'any time' in text_lower:
        return 'anytime'
    
    return None


def extract_student_info(interaction: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract all student information from an interaction."""
    # Get full transcript text
    transcript_text = get_full_transcript_text(interaction)
    
    # Also check summary if available
    summary = interaction.get("summary") or interaction.get("transcript_summary") or ""
    full_text = f"{transcript_text}\n{summary}"
    
    # Extract information
    student_name = extract_name(full_text)
    student_email = extract_email(full_text)
    student_phone = extract_phone(full_text)
    best_time = extract_best_time(full_text)
    
    return {
        "student_name": student_name,
        "student_email": student_email,
        "student_phone": student_phone,
        "best_time_to_call": best_time
    }


def main():
    """Main backfill script."""
    print("🔄 Starting student information backfill...")
    print(f"📁 Loading interactions from: {INTERACTIONS_FILE}")
    
    interactions = load_interactions()
    if not interactions:
        print("❌ No interactions found")
        return
    
    print(f"✅ Loaded {len(interactions)} interactions")
    print()
    
    updated_count = 0
    skipped_count = 0
    
    for interaction in interactions:
        conv_id = interaction.get("id", "unknown")
        
        # Check if already has student info
        has_name = interaction.get("user_name") or interaction.get("student_name")
        has_email = interaction.get("user_email") or interaction.get("student_email")
        
        if has_name and has_email:
            skipped_count += 1
            continue
        
        # Extract student information
        extracted = extract_student_info(interaction)
        
        # Only update if we found something
        if extracted["student_name"] or extracted["student_email"] or extracted["student_phone"]:
            print(f"📝 Updating {conv_id[:20]}...")
            print(f"   Name:  {extracted['student_name'] or 'N/A'}")
            print(f"   Email: {extracted['student_email'] or 'N/A'}")
            print(f"   Phone: {extracted['student_phone'] or 'N/A'}")
            print()
            
            # Update fields (preserve existing user_name/user_email if present)
            if extracted["student_name"]:
                if not interaction.get("user_name"):
                    interaction["user_name"] = extracted["student_name"]
            
            if extracted["student_email"]:
                if not interaction.get("user_email"):
                    interaction["user_email"] = extracted["student_email"]
            
            # Always update extracted_data_json with new info
            if not interaction.get("extracted_data_json"):
                interaction["extracted_data_json"] = {}
            
            if extracted["student_name"]:
                interaction["extracted_data_json"]["student_name"] = extracted["student_name"]
                interaction["extracted_data_json"]["user_name"] = extracted["student_name"]
            
            if extracted["student_email"]:
                interaction["extracted_data_json"]["student_email"] = extracted["student_email"]
                interaction["extracted_data_json"]["user_email"] = extracted["student_email"]
            
            if extracted["student_phone"]:
                interaction["extracted_data_json"]["student_phone"] = extracted["student_phone"]
            
            if extracted["best_time_to_call"]:
                interaction["extracted_data_json"]["best_time_to_call"] = extracted["best_time_to_call"]
            
            updated_count += 1
    
    print()
    print("=" * 60)
    print(f"✅ Updated: {updated_count} conversations")
    print(f"⏭️  Skipped: {skipped_count} conversations (already had data)")
    print(f"📊 Total:   {len(interactions)} conversations")
    print("=" * 60)
    
    if updated_count > 0:
        print()
        save_interactions(interactions)
        print()
        print("✅ Backfill complete! Student information extracted from transcripts.")
    else:
        print()
        print("ℹ️  No updates needed - all interactions already have student info.")


if __name__ == "__main__":
    main()

