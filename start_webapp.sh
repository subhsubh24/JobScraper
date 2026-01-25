#!/bin/bash
# Start JobScraper Web Application

echo "======================================"
echo "   Starting JobScraper Web App"
echo "======================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if database exists
if [ ! -f "data/jobscraper.db" ]; then
    echo "Database not found. Initializing..."
    python cli.py init
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  Warning: OPENAI_API_KEY not found in .env"
    echo "   Prep pack generation will fail without it."
    echo ""
fi

echo "Starting Flask web server..."
echo ""
echo "🌐 Web App will be available at:"
echo "   http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
