#!/bin/bash

# Configuration
VENV_DIR="venv"
MAIN_FILE="main.py"
REQ_FILE="requirements.txt"

echo "🚀 Starting FastAPI Backend Locally..."

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create virtual environment."
        exit 1
    fi
    
    echo "🔌 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    if [ -f "$REQ_FILE" ]; then
        echo "� Installing dependencies from $REQ_FILE..."
        pip install --upgrade pip
        pip install -r "$REQ_FILE"
    else
        echo "⚠️ Warning: $REQ_FILE not found. Skipping dependency installation."
    fi
else
    echo "�🔌 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Verify activation
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate virtual environment."
    exit 1
fi

# Run the server
echo "🏃 Starting FastAPI server..."
exec python3 "$MAIN_FILE"
