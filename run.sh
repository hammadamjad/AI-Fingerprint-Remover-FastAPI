#!/bin/bash

# Configuration
VENV_DIR="venv"
MAIN_FILE="main.py"

echo "🚀 Starting FastAPI Backend Locally..."

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Error: Virtual environment '$VENV_DIR' not found."
    echo "Please create it first (e.g., python3 -m venv venv && pip install -r requirements.txt)"
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Verify activation
if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate virtual environment."
    exit 1
fi

# Run the server
echo "🏃 Starting FastAPI server..."
exec python3 "$MAIN_FILE"

# Note: main.py uses uvicorn.run(app, host="127.0.0.1", port=8000)
