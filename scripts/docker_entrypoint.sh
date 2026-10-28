#!/bin/bash
set -e

echo "=================================================="
echo "🚀 Initializing OrchardIQ Autonomous Data Platform"
echo "=================================================="

# Check if synthetic warehouse exists, if not generate lightweight dataset (--scale 0.2)
if [ ! -f "data/warehouse/orchard_dw.duckdb" ] && [ ! -d "data/warehouse/marts" ]; then
    echo "📦 Generating synthetic star-schema lakehouse dataset (scale ~0.2)..."
    python -m src.data_gen.generator --scale 0.2 --seed 42
    echo "✅ Synthetic star-schema warehouse generated."
fi

# Check if Chroma vector store index exists
if [ ! -d "data/chroma" ]; then
    echo "🔍 Indexing knowledge base markdown documents and support tickets into ChromaDB..."
    python -m src.rag.indexer
    echo "✅ Knowledge base vectors indexed."
fi

echo "🟢 Launching OrchardIQ FastAPI backend on port 8000..."
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
