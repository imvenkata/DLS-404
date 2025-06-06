#!/bin/bash

# DLS-404 Chainlit Frontend Startup Script
# This script sets up the environment and starts the Chainlit application

set -e  # Exit on any error

echo "🚀 Starting DLS-404 Chainlit Frontend..."

# Check if we're in the correct directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the chainlit-frontend directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if parent directory .env exists and copy if needed
if [ -f "../.env" ] && [ ! -f ".env" ]; then
    echo "📄 Copying environment file from parent directory..."
    cp ../.env .env
fi

# Check for required environment variables
echo "🔍 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one with your Azure and GitLab credentials."
    echo "   See README.md for required environment variables."
fi

# Run the Chainlit application
echo "🎉 Starting Chainlit application..."
echo "   - Application will be available at: http://localhost:8000"
echo "   - Press Ctrl+C to stop"
echo ""

# Start with watch mode for development
chainlit run app.py -w --host 0.0.0.0 --port 8000 