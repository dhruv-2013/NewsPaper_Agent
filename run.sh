#!/bin/bash

# Startup script for the News Aggregation System

echo "🚀 Starting AI-Powered News Aggregation System..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env file..."
    echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
    echo "NEWS_API_KEY=your_news_api_key_here" >> .env
    echo "USE_OPENAI=true" >> .env
    echo "Please edit .env and add your API keys before running."
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create templates directory if it doesn't exist
mkdir -p templates

# Run the application
echo ""
echo "✅ All dependencies installed!"
echo "🌐 Starting server..."
echo "📱 Open http://localhost:8000 in your browser"
echo ""
python main.py

