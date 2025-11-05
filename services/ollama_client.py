"""
Ollama Client Service
Handles communication with Ollama API on localhost:40000
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:40000"):
        """
        Initialize Ollama client
        
        Args:
            base_url: Ollama API base URL (default: localhost:40000)
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.model = "qwen3:8b"  # Default model
        
    async def check_health(self) -> Dict[str, Any]:
        """
        Check Ollama service health
        
        Returns:
            Dict with health status and available models
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "available_models": models,
                "default_model": self.model,
                "timestamp": datetime.now().isoformat()
            }
            
        except httpx.ConnectError:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to Ollama service",
                "base_url": self.base_url,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "base_url": self.base_url,
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        thinking_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate response from Ollama
        
        Args:
            prompt: Input prompt
            model: Model to use (default: qwen3:8b)
            thinking_mode: Enable thinking mode for deeper reasoning
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Dict with response data and metadata
        """
        if model is None:
            model = self.model
            
        # Prepare prompt based on thinking mode
        if thinking_mode:
            formatted_prompt = f"{prompt}\n\n/think"
        else:
            formatted_prompt = f"{prompt}\n\n/no_think"
        
        payload = {
            "model": model,
            "prompt": formatted_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        start_time = datetime.now()
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "model": model,
                "thinking_mode": thinking_mode,
                "response_time": response_time,
                "timestamp": end_time.isoformat(),
                "metadata": {
                    "prompt_length": len(prompt),
                    "response_length": len(result.get("response", "")),
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            
        except httpx.ConnectError:
            return {
                "success": False,
                "error": "Cannot connect to Ollama service",
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_streaming(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        thinking_mode: bool = False
    ):
        """
        Generate streaming response from Ollama
        
        Args:
            prompt: Input prompt
            model: Model to use
            thinking_mode: Enable thinking mode
            
        Yields:
            Dict with streaming response chunks
        """
        if model is None:
            model = self.model
            
        # Prepare prompt based on thinking mode
        if thinking_mode:
            formatted_prompt = f"{prompt}\n\n/think"
        else:
            formatted_prompt = f"{prompt}\n\n/no_think"
        
        payload = {
            "model": model,
            "prompt": formatted_prompt,
            "stream": True,
            "options": {
                "temperature": 0.7
            }
        }
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = response.json()
                            yield {
                                "chunk": chunk.get("response", ""),
                                "done": chunk.get("done", False),
                                "model": model,
                                "thinking_mode": thinking_mode
                            }
                        except:
                            continue
                            
        except Exception as e:
            yield {
                "error": str(e),
                "done": True,
                "model": model
            }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models
        
        Returns:
            List of model information
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models_data = response.json()
            return models_data.get("models", [])
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global instance
ollama_client = OllamaClient()

# Convenience functions
async def check_ollama_health() -> Dict[str, Any]:
    """Check Ollama health"""
    return await ollama_client.check_health()

async def generate_response(
    prompt: str, 
    model: str = "qwen3:8b",
    thinking_mode: bool = False
) -> Dict[str, Any]:
    """Generate response from Ollama"""
    return await ollama_client.generate(
        prompt=prompt,
        model=model,
        thinking_mode=thinking_mode
    )

async def get_available_models() -> List[Dict[str, Any]]:
    """Get list of available models"""
    return await ollama_client.list_models()
