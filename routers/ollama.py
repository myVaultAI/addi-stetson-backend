"""
Ollama API Router
Endpoints for Ollama integration
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
import asyncio
from services.ollama_client import ollama_client, generate_response, check_ollama_health

router = APIRouter(prefix="/api/ollama", tags=["ollama"])

@router.get("/health")
async def ollama_health():
    """Check Ollama service health"""
    try:
        health_status = await check_ollama_health()
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/generate")
async def generate_ollama_response(
    prompt: str,
    model: Optional[str] = "qwen3:8b",
    thinking_mode: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 1000
):
    """Generate response from Ollama"""
    try:
        result = await generate_response(
            prompt=prompt,
            model=model,
            thinking_mode=thinking_mode
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500, 
                detail=f"Ollama generation failed: {result.get('error', 'Unknown error')}"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        models = await ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.post("/test")
async def test_ollama_connection():
    """Test Ollama connection with simple prompt"""
    try:
        test_prompt = "Hello, can you respond with just 'Connection successful'?"
        result = await generate_response(
            prompt=test_prompt,
            model="qwen3:8b",
            thinking_mode=False
        )
        
        if result.get("success", False):
            return {
                "status": "success",
                "message": "Ollama connection test passed",
                "response": result.get("response", ""),
                "response_time": result.get("response_time", 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Test failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")
