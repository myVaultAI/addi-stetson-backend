"""
title: Stetson Knowledge Query
description: Query Stetson University information from curated knowledge base via DME-CPH backend
author: DME-CPH Team
version: 1.0.0
requirements: httpx
"""

import httpx
from typing import Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class Tools:
    """
    Stetson Knowledge Query Tool - Production Grade
    
    Features:
    - Connection to FastAPI backend
    - Cached responses (via backend)
    - Confidence scoring
    - Source attribution
    - Graceful error handling
    """
    
    class Valves(BaseModel):
        """Configuration for Stetson Knowledge Tool"""
        BACKEND_URL: str = Field(
            default="http://localhost:44000",
            description="DME-CPH Backend API URL"
        )
        TIMEOUT: int = Field(
            default=30,
            description="Request timeout in seconds"
        )
        MIN_CONFIDENCE: float = Field(
            default=0.5,
            description="Minimum confidence threshold (0.0-1.0)"
        )
    
    def __init__(self):
        self.valves = self.Valves()
        self.citation = True
    
    async def query_stetson_knowledge(
        self,
        question: str,
        __user__: dict = None,
        __event_emitter__=None
    ) -> str:
        """
        Query Stetson University knowledge base for accurate, curated information.
        
        Use this for questions about:
        - Academic programs and majors
        - Admissions requirements and deadlines
        - Campus life and student services
        - Financial aid and scholarships
        - Campus facilities and resources
        
        :param question: The question to search for in Stetson knowledge base
        :return: Detailed answer from curated Stetson information
        """
        
        # Validate question length
        if len(question) > 500:
            return "❌ Question is too long. Please keep questions under 500 characters."
        
        # Emit status update
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "Searching Stetson knowledge base...",
                    "done": False
                }
            })
        
        try:
            # Call our RAG endpoint with connection pooling
            async with httpx.AsyncClient(timeout=self.valves.TIMEOUT) as client:
                response = await client.post(
                    f"{self.valves.BACKEND_URL}/api/rag/query",
                    json={
                        "question": question,
                        "collection": "knowledge_base",
                        "n_results": 3
                    }
                )
                response.raise_for_status()
                result = response.json()
                data = result.get("data", {})
            
            # Check confidence
            confidence = data.get("confidence", 0.0)
            cached = data.get("cached", False)
            response_time = data.get("response_time_ms", 0)
            
            # Emit completion status
            if __event_emitter__:
                cache_indicator = " ⚡(cached)" if cached else ""
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"✓ Found information ({response_time:.0f}ms, {confidence:.0%} confidence){cache_indicator}",
                        "done": True
                    }
                })
            
            # Format response
            if data.get("found"):
                context = data.get("context", "")
                sources = data.get("sources", [])
                
                # Add confidence indicator
                if confidence >= 0.8:
                    confidence_emoji = "🎯"
                elif confidence >= 0.6:
                    confidence_emoji = "✓"
                else:
                    confidence_emoji = "~"
                
                response_text = f"{context}\n\n"
                
                # Format sources with links if available
                if sources:
                    response_text += f"**Sources** {confidence_emoji}:\n"
                    for i, source in enumerate(sources, 1):
                        if isinstance(source, dict):
                            source_text = source.get('text', source.get('filename', 'Unknown'))
                            source_url = source.get('url')
                            
                            if source_url:
                                response_text += f"{i}. [{source_text}]({source_url})\n"
                            else:
                                response_text += f"{i}. {source_text}\n"
                        else:
                            response_text += f"{i}. {source}\n"
                
                # Low confidence warning
                if confidence < self.valves.MIN_CONFIDENCE:
                    response_text += "\n*Note: Lower confidence result. Consider refining your query or asking differently.*\n"
                
                return response_text
            else:
                return (
                    "I don't have specific information about that in my Stetson knowledge base. "
                    "Let me try a web search instead, or you can rephrase your question."
                )
        
        except httpx.TimeoutException:
            # Emit timeout error
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": "Request timed out",
                        "done": True
                    }
                })
            return (
                "⏱️ The knowledge base search is taking longer than expected. "
                "Try rephrasing your question to be more specific, or try again in a moment."
            )
        
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"Error {status_code}",
                        "done": True
                    }
                })
            
            if status_code >= 500:
                return "🚨 The knowledge base service is temporarily unavailable. Please try again shortly."
            else:
                return f"❌ Request failed. Please try again or contact support if the issue persists."
        
        except Exception as e:
            logger.exception(f"Unexpected error in Stetson Knowledge tool: {str(e)}")
            
            # Emit generic error
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": "Unexpected error",
                        "done": True
                    }
                })
            
            return (
                "❌ I encountered an unexpected error processing your question. "
                "Please try rephrasing, or contact an admissions counselor for direct assistance."
            )

