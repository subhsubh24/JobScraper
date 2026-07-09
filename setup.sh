#!/bin/bash
# JobScraper setup script

set -e

echo "======================================"
echo "   JobScraper Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY (optional — AI degrades gracefully without it)"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/logs
mkdir -p data/cache

# Initialize database
echo ""
echo "Initializing database..."
python scripts/init_db.py

echo ""
echo "======================================"
echo "   Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY (optional — AI degrades gracefully without it)"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Start the API: ./start_api.sh   (or: python -m uvicorn asgi:app --reload)"
echo "4. Run the tests: pytest"
echo ""
echo "The web app lives in web/ (npm run dev); the mobile app in mobile/ (npx expo start)."
echo ""
