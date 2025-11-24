"""
Topic Analysis Service using Google Gemini AI
Analyzes conversation transcripts to identify Stetson University topics
"""

import os
import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Stetson University Topic Definitions (matching the conversation tracker)
STETSON_TOPICS = [
    # Student Services (most common in phone calls)
    {"category": "Student Services", "topic": "Financial Aid and Scholarships"},
    {"category": "Student Services", "topic": "Admissions"},
    {"category": "Student Services", "topic": "Housing and Residential Life"},
    {"category": "Student Services", "topic": "Academic Advising"},
    {"category": "Student Services", "topic": "Career Services"},
    {"category": "Student Services", "topic": "Athletics"},
    {"category": "Student Services", "topic": "International Programs and Study Abroad"},

    # Popular Undergraduate Majors - Science & Technology
    {"category": "Undergraduate Majors", "topic": "Marine Biology and Oceanography"},
    {"category": "Undergraduate Majors", "topic": "Biology"},
    {"category": "Undergraduate Majors", "topic": "Computer Science"},
    {"category": "Undergraduate Majors", "topic": "Environmental Science"},
    {"category": "Undergraduate Majors", "topic": "Chemistry"},

    # Popular Undergraduate Majors - Business
    {"category": "Undergraduate Majors", "topic": "Business Administration"},
    {"category": "Undergraduate Majors", "topic": "Accounting"},
    {"category": "Undergraduate Majors", "topic": "Marketing"},
    {"category": "Undergraduate Majors", "topic": "Finance"},

    # Popular Undergraduate Majors - Arts & Humanities
    {"category": "Undergraduate Majors", "topic": "Communications"},
    {"category": "Undergraduate Majors", "topic": "Psychology"},
    {"category": "Undergraduate Majors", "topic": "English"},
    {"category": "Undergraduate Majors", "topic": "History"},

    # Graduate & Professional Programs
    {"category": "Graduate Degrees", "topic": "MBA"},
    {"category": "Graduate Degrees", "topic": "MAcc"},
    {"category": "Law Degrees", "topic": "Juris Doctor"},
    {"category": "Law Degrees", "topic": "LLM in Elder Law"},

    # Pre-Professional Programs
    {"category": "Pre-Professional Programs", "topic": "Pre-Law"},
    {"category": "Pre-Professional Programs", "topic": "Pre-Health"},
    {"category": "Pre-Professional Programs", "topic": "Pre-Engineering"},

    # Professional Partnerships
    {"category": "Professional Partnerships", "topic": "Nursing"},
    {"category": "Professional Partnerships", "topic": "Physical Therapy"},
    {"category": "Professional Partnerships", "topic": "Pharmacy"},

    # Music Programs
    {"category": "Music Programs", "topic": "Music"},
    {"category": "Music Programs", "topic": "Music Performance"},
]


class TopicAnalyzer:
    """Analyzes conversation transcripts using Google Gemini AI"""

    def __init__(self):
        """Initialize the Gemini AI client"""
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_GEMINI_API_KEY not set - topic analysis will not work")
            self.ai_available = False
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.ai_available = True
        logger.info("Topic Analyzer initialized with Gemini AI")

    def analyze_conversation(self, transcript: List[Dict[str, Any]]) -> str:
        """
        Analyze a conversation transcript and return the primary topic

        Args:
            transcript: List of conversation turns with speaker and text

        Returns:
            The primary topic mentioned in the conversation
        """
        if not self.ai_available:
            logger.warning("Gemini AI not available - returning default topic")
            return "General Inquiry"

        try:
            # Build transcript text from conversation turns
            transcript_text = self._build_transcript_text(transcript)

            if not transcript_text or len(transcript_text) < 20:
                return "General Inquiry"

            # Get topic from Gemini
            topic = self._analyze_with_gemini(transcript_text)
            return topic

        except Exception as e:
            logger.error(f"Error analyzing conversation topic: {str(e)}")
            return "General Inquiry"

    def _build_transcript_text(self, transcript: List[Dict[str, Any]]) -> str:
        """Build a readable transcript from conversation turns"""
        lines = []
        for turn in transcript:
            speaker = turn.get("speaker", "unknown")
            text = turn.get("text", "")
            if text:
                lines.append(f"{speaker}: {text}")
        return "\n".join(lines)

    def _analyze_with_gemini(self, transcript_text: str) -> str:
        """Use Gemini AI to analyze the transcript and identify the primary topic"""

        # Build topics list for the prompt
        topics_list = [t["topic"] for t in STETSON_TOPICS]
        topics_string = ", ".join(topics_list)

        prompt = f"""Analyze this Stetson University phone conversation and identify the PRIMARY topic discussed.

AVAILABLE TOPICS:
{topics_string}

CONVERSATION TRANSCRIPT:
---
{transcript_text}
---

INSTRUCTIONS:
1. Read the entire conversation carefully
2. Identify which ONE topic from the list is the MAIN focus of the conversation
3. Return ONLY the exact topic name from the list above
4. If multiple topics are mentioned, choose the one that is most prominently discussed
5. If no topics from the list are clearly discussed, return "General Inquiry"

PRIMARY TOPIC:"""

        try:
            response = self.model.generate_content(prompt)
            topic = response.text.strip()

            # Validate that the returned topic is in our list
            valid_topics = [t["topic"] for t in STETSON_TOPICS] + ["General Inquiry"]

            if topic not in valid_topics:
                logger.warning(f"Gemini returned invalid topic: {topic}")
                # Try to find a partial match
                topic_lower = topic.lower()
                for valid_topic in valid_topics:
                    if valid_topic.lower() in topic_lower or topic_lower in valid_topic.lower():
                        logger.info(f"Found partial match: {valid_topic}")
                        return valid_topic
                return "General Inquiry"

            logger.info(f"Gemini identified topic: {topic}")
            return topic

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return "General Inquiry"


# Global instance
_topic_analyzer = None

def get_topic_analyzer() -> TopicAnalyzer:
    """Get or create the global TopicAnalyzer instance"""
    global _topic_analyzer
    if _topic_analyzer is None:
        _topic_analyzer = TopicAnalyzer()
    return _topic_analyzer
