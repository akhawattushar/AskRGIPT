#!/bin/bash

echo "🚀 Starting AskRGIPT setup..."

# Check if chroma_db already exists
if [ ! -d "chroma_db" ]; then
    echo "📊 Building vector store from PDFs..."
    python populate_vector_store.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Vector store built successfully!"
    else
        echo "❌ Vector store build failed!"
    fi
else
    echo "✅ Vector store already exists, skipping build..."
fi

echo "🎓 Starting AskRGIPT app..."
