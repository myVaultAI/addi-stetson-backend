#!/bin/bash

# Ingest Stetson Knowledge Documents via API
# This script uses the RAG API endpoint to ingest documents

echo "======================================================================"
echo "STETSON KNOWLEDGE INGESTION (Via API)"
echo "======================================================================"
echo ""

# Base paths
KNOWLEDGE_DIR="/Users/jason/Documents/Vault AI/knowledge/Addi/stetson_knowledge"
API_URL="http://localhost:44000/api/rag/ingest"

# Check if backend is running
echo "🔍 Checking backend..."
if ! curl -s http://localhost:44000/health > /dev/null; then
    echo "❌ Backend is not running on port 44000"
    echo "   Please start the backend first: cd /Users/jason/Projects/addi_demo/addi_backend && python main.py"
    exit 1
fi
echo "✓ Backend is running"
echo ""

# Count documents
doc_count=$(ls -1 "$KNOWLEDGE_DIR"/*.md 2>/dev/null | grep -v README | wc -l | tr -d ' ')
echo "📁 Found $doc_count documents in: $KNOWLEDGE_DIR"
echo ""

# Ingest each document
echo "----------------------------------------------------------------------"
echo "INGESTING DOCUMENTS"
echo "----------------------------------------------------------------------"
echo ""

success=0
failed=0

for doc_file in "$KNOWLEDGE_DIR"/*.md; do
    filename=$(basename "$doc_file")
    
    # Skip README
    if [ "$filename" = "README.md" ]; then
        continue
    fi
    
    # Extract document ID (filename without extension)
    doc_id="${filename%.md}"
    
    echo "📄 Processing: $filename"
    
    # Read file content and escape for JSON
    content=$(cat "$doc_file" | jq -Rs .)
    
    # Prepare JSON payload
    json_payload=$(cat <<EOF
{
  "document": $content,
  "document_id": "$doc_id",
  "collection": "stetson_knowledge",
  "metadata": {
    "source": "$filename",
    "type": "knowledge_doc"
  }
}
EOF
)
    
    # Make API call
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Check if successful
    if echo "$response" | jq -e '.success == true' > /dev/null 2>&1; then
        collection_count=$(echo "$response" | jq -r '.collection_count')
        echo "  ✓ Ingested successfully (collection now has $collection_count documents)"
        ((success++))
    else
        error=$(echo "$response" | jq -r '.detail // "Unknown error"')
        echo "  ❌ Failed: $error"
        ((failed++))
    fi
    echo ""
done

# Summary
echo "======================================================================"
echo "SUMMARY"
echo "======================================================================"
echo "✅ Successfully ingested: $success documents"
if [ $failed -gt 0 ]; then
    echo "❌ Failed: $failed documents"
fi
echo ""

# Test query
echo "----------------------------------------------------------------------"
echo "TESTING RAG QUERY"
echo "----------------------------------------------------------------------"
echo ""
echo "Test Query: 'What are the admissions requirements?'"
echo ""

query_response=$(curl -s -X POST "http://localhost:44000/api/rag/query" \
    -H "Content-Type: application/json" \
    -d '{"question": "What are the admissions requirements for Stetson University?", "collection": "stetson_knowledge", "n_results": 3}')

if echo "$query_response" | jq -e '.success == true' > /dev/null 2>&1; then
    echo "✓ Query successful!"
    confidence=$(echo "$query_response" | jq -r '.data.confidence // 0')
    echo "  Confidence: ${confidence}%"
    echo ""
    # Show first 200 chars of context
    context=$(echo "$query_response" | jq -r '.data.context // "No context"' | head -c 200)
    echo "  Context preview:"
    echo "  ${context}..."
else
    echo "❌ Query failed"
    echo "$query_response" | jq .
fi

echo ""
echo "======================================================================"
echo "✅ INGESTION COMPLETE"
echo "======================================================================"

exit 0

