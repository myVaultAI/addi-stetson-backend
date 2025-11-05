import httpx
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ElevenLabsAPIClient:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set")
        
        self.base_url = "https://api.elevenlabs.io/v1/convai"
        self.headers = {"xi-api-key": self.api_key}
        logger.info(f"ElevenLabs API client initialized with base URL: {self.base_url}")
    
    async def get_all_conversations(self, agent_id: str) -> List[Dict]:
        """Pull all historical conversations for an agent"""
        conversations = []
        next_cursor = None
        page_count = 0
        
        logger.info(f"Fetching conversations for agent: {agent_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                page_count += 1
                params = {"page_size": 100}
                if agent_id:
                    params["agent_id"] = agent_id
                if next_cursor:
                    params["cursor"] = next_cursor
                
                logger.info(f"Fetching page {page_count}, cursor: {next_cursor}")
                
                try:
                    response = await client.get(
                        f"{self.base_url}/conversations",
                        headers=self.headers,
                        params=params
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    page_conversations = data.get("conversations", [])
                    conversations.extend(page_conversations)
                    
                    logger.info(f"Page {page_count}: Found {len(page_conversations)} conversations")
                    
                    if not data.get("has_more"):
                        logger.info("No more pages available")
                        break
                    next_cursor = data.get("next_cursor")
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error fetching conversations: {e.response.status_code} - {e.response.text}")
                    raise
                except Exception as e:
                    logger.error(f"Error fetching conversations: {str(e)}")
                    raise
        
        logger.info(f"Total conversations fetched: {len(conversations)}")
        return conversations
    
    async def get_conversation_details(self, conversation_id: str) -> Dict:
        """Get full details for a specific conversation"""
        logger.info(f"Fetching details for conversation: {conversation_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/conversations/{conversation_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Successfully fetched details for {conversation_id}")
                return data
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching conversation {conversation_id}: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error fetching conversation {conversation_id}: {str(e)}")
                raise
    
    async def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/conversations",
                    headers=self.headers,
                    params={"page_size": 1}
                )
                response.raise_for_status()
                logger.info("API connection test successful")
                return True
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            return False
