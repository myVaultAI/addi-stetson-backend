"""
Ingest Stetson University Knowledge Documents into ChromaDB
This script loads the comprehensive Stetson knowledge base into the RAG system.
"""

import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def ingest_stetson_knowledge():
    """Ingest Stetson knowledge documents into ChromaDB"""
    
    print("=" * 70)
    print("STETSON KNOWLEDGE BASE INGESTION")
    print("=" * 70)
    
    # ChromaDB connection
    chroma_path = "/Users/jason/Documents/Vault AI/projects/vault-agent-hub/rag-system/chroma_db"
    print(f"\n📁 Connecting to ChromaDB at: {chroma_path}")
    
    try:
        client = chromadb.PersistentClient(path=chroma_path)
        print("✓ Connected to ChromaDB")
    except Exception as e:
        print(f"❌ Failed to connect to ChromaDB: {e}")
        return False
    
    # Get or create collection
    collection_name = "stetson_knowledge"
    print(f"\n📚 Collection: {collection_name}")
    
    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "Stetson University comprehensive knowledge base for Addi AI assistant",
                "source": "DME-CPH Platform",
                "created_date": "2025-10-22",
                "version": "1.0"
            }
        )
        print(f"✓ Collection ready (current count: {collection.count()} documents)")
    except Exception as e:
        print(f"❌ Failed to access collection: {e}")
        return False
    
    # Knowledge documents location
    knowledge_dir = Path("/Users/jason/Documents/Vault AI/knowledge/Addi/stetson_knowledge")
    print(f"\n📖 Reading documents from: {knowledge_dir}")
    
    if not knowledge_dir.exists():
        print(f"❌ Knowledge directory not found: {knowledge_dir}")
        return False
    
    # Find all markdown files (except README)
    md_files = [f for f in knowledge_dir.glob("*.md") if f.name != "README.md"]
    
    if not md_files:
        print("⚠️  No markdown files found in knowledge directory")
        return False
    
    print(f"✓ Found {len(md_files)} documents to ingest")
    
    # Ingest each document
    print("\n" + "-" * 70)
    print("INGESTING DOCUMENTS")
    print("-" * 70)
    
    ingested_count = 0
    failed_count = 0
    
    for md_file in md_files:
        try:
            print(f"\n📄 Processing: {md_file.name}")
            
            # Read document content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract document ID from content (if available)
            doc_id_line = [line for line in content.split('\n') if line.startswith('**Document ID:**')]
            doc_id = doc_id_line[0].split('**Document ID:**')[1].strip() if doc_id_line else md_file.stem
            
            # Extract category
            category_line = [line for line in content.split('\n') if line.startswith('**Category:**')]
            category = category_line[0].split('**Category:**')[1].strip() if category_line else "General"
            
            # Extract keywords
            keywords_line = [line for line in content.split('\n') if line.startswith('**Keywords:**')]
            keywords = keywords_line[0].split('**Keywords:**')[1].strip() if keywords_line else ""
            
            # Prepare metadata
            metadata = {
                "source": md_file.name,
                "document_id": doc_id,
                "category": category,
                "keywords": keywords,
                "type": "knowledge_doc",
                "ingestion_date": "2025-10-22"
            }
            
            # Add to collection
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[md_file.stem]
            )
            
            print(f"  ✓ Document ID: {doc_id}")
            print(f"  ✓ Category: {category}")
            print(f"  ✓ Content length: {len(content)} characters")
            print(f"  ✓ Ingested successfully")
            
            ingested_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to ingest {md_file.name}: {e}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)
    print(f"\n✅ Successfully ingested: {ingested_count} documents")
    if failed_count > 0:
        print(f"❌ Failed to ingest: {failed_count} documents")
    
    # Final collection stats
    final_count = collection.count()
    print(f"\n📊 Collection '{collection_name}' now contains: {final_count} documents")
    
    # Test query
    print("\n" + "-" * 70)
    print("TESTING RAG QUERY")
    print("-" * 70)
    
    test_query = "What are the admissions requirements for Stetson University?"
    print(f"\nTest Query: \"{test_query}\"")
    
    try:
        results = collection.query(
            query_texts=[test_query],
            n_results=3
        )
        
        if results and results['documents']:
            print(f"\n✓ Query successful!")
            print(f"  Found {len(results['documents'][0])} relevant chunks")
            print(f"  Top result preview: {results['documents'][0][0][:200]}...")
        else:
            print("⚠️  Query returned no results")
    except Exception as e:
        print(f"❌ Test query failed: {e}")
    
    print("\n" + "=" * 70)
    print("✅ INGESTION COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = ingest_stetson_knowledge()
    sys.exit(0 if success else 1)

