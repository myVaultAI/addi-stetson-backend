"""
Simple ingestion script for Stetson knowledge documents
"""
import sys
from pathlib import Path

# Use the RAG service directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag_service import rag_service

def ingest_documents():
    """Ingest Stetson knowledge documents"""
    
    print("=" * 70)
    print("STETSON KNOWLEDGE INGESTION (Simple Method)")
    print("=" * 70)
    
    # Knowledge documents path
    knowledge_dir = Path("/Users/jason/Documents/Vault AI/knowledge/Addi/stetson_knowledge")
    
    print(f"\n📁 Reading from: {knowledge_dir}")
    
    if not knowledge_dir.exists():
        print(f"❌ Directory not found: {knowledge_dir}")
        return False
    
    # Find markdown files
    md_files = [f for f in knowledge_dir.glob("*.md") if f.name != "README.md"]
    
    if not md_files:
        print("❌ No markdown files found")
        return False
    
    print(f"✓ Found {len(md_files)} documents")
    
    # Get ChromaDB client
    try:
        client = rag_service.get_chromadb_client()
        print("✓ Connected to ChromaDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False
    
    # Get or create collection
    try:
        collection = client.get_or_create_collection(
            name="stetson_knowledge",
            metadata={
                "description": "Stetson University knowledge base",
                "created": "2025-10-22"
            }
        )
        print(f"✓ Collection ready: stetson_knowledge (current count: {collection.count()})")
    except Exception as e:
        print(f"❌ Failed to access collection: {e}")
        return False
    
    # Ingest each document
    print("\n" + "-" * 70)
    print("INGESTING DOCUMENTS")
    print("-" * 70)
    
    success_count = 0
    
    for md_file in md_files:
        try:
            print(f"\n📄 {md_file.name}")
            
            # Read content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add to collection
            collection.add(
                documents=[content],
                metadatas=[{
                    "source": md_file.name,
                    "type": "knowledge_doc"
                }],
                ids=[md_file.stem]
            )
            
            print(f"  ✓ Ingested ({len(content)} chars)")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully ingested: {success_count}/{len(md_files)} documents")
    print(f"📊 Collection now contains: {collection.count()} documents")
    print("=" * 70)
    
    # Test query
    print("\n🔍 Testing query...")
    try:
        results = collection.query(
            query_texts=["What are the admissions requirements?"],
            n_results=1
        )
        if results and results['documents']:
            print("✓ Query successful!")
            print(f"  Preview: {results['documents'][0][0][:100]}...")
        else:
            print("⚠️  No results returned")
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    return success_count == len(md_files)


if __name__ == "__main__":
    success = ingest_documents()
    sys.exit(0 if success else 1)

