"""
RAG API Router
Endpoints for knowledge base queries with production-grade features
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from services.rag_service import rag_service, query_rag, check_rag_health

router = APIRouter(prefix="/api/rag", tags=["rag"])


class QueryRequest(BaseModel):
    """Request model for RAG queries"""
    question: str = Field(..., min_length=1, max_length=500, description="Question to search for")
    collection: str = Field(default="knowledge_base", description="ChromaDB collection name")
    n_results: Optional[int] = Field(default=None, ge=1, le=10, description="Number of results")


@router.post("/query")
async def query_knowledge(request: QueryRequest):
    """
    Query knowledge base for relevant information
    
    Features:
    - LRU cache with TTL (50-100x faster for repeats)
    - Retry logic with exponential backoff
    - Confidence scoring
    - Source attribution
    """
    try:
        result = await query_rag(
            question=request.question,
            collection=request.collection,
            n_results=request.n_results
        )
        
        if result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"RAG query failed: {result.get('error')}"
            )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/health")
async def rag_health():
    """Check RAG system health"""
    try:
        health_status = await check_rag_health()
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.post("/clear-cache")
async def clear_cache():
    """Clear the RAG query cache"""
    try:
        result = rag_service.clear_cache()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cache clear failed: {str(e)}"
        )


@router.get("/cache-stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        stats = rag_service.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.get("/collections")
async def list_collections():
    """List available ChromaDB collections"""
    try:
        health = await check_rag_health()
        if health.get("status") == "healthy":
            return {
                "collections": health.get("collections", [])
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="RAG system unhealthy"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list collections: {str(e)}"
        )


class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    document: str = Field(..., description="Document content to ingest")
    document_id: str = Field(..., description="Unique document ID")
    collection: str = Field(default="stetson_knowledge", description="Collection name")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")


@router.post("/ingest")
async def ingest_document(request: IngestRequest):
    """
    Ingest a single document into ChromaDB collection
    
    This endpoint allows adding documents to the knowledge base
    without running separate ingestion scripts.
    """
    try:
        # Get ChromaDB client
        client = rag_service.get_chromadb_client()
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name=request.collection,
            metadata={
                "description": f"{request.collection} knowledge base",
                "updated": "2025-10-22"
            }
        )
        
        # Prepare metadata
        metadata = request.metadata or {}
        metadata["ingested_via"] = "api"
        
        # Add document
        collection.add(
            documents=[request.document],
            metadatas=[metadata],
            ids=[request.document_id]
        )
        
        return {
            "success": True,
            "message": f"Document '{request.document_id}' ingested successfully",
            "collection": request.collection,
            "collection_count": collection.count()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )

