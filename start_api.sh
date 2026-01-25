#!/bin/bash
# Start Career Operator API for mobile app

echo "🚀 Starting Career Operator API..."
echo ""

# Check if running in development
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and fill in your API keys"
    exit 1
fi

# Start API server
echo "✓ Starting FastAPI server on http://0.0.0.0:8000"
echo "✓ API docs available at http://0.0.0.0:8000/docs"
echo ""

python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
