#!/bin/bash

# Site Safety Monitor - Development Startup Script
# This replaces docker-compose for WebContainer environment

echo "🚀 Site Safety Monitor - Development Environment"
echo "================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if we're in the project root
if [ ! -f "main.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    python3 -m pip install -r requirements.txt --user
else
    echo "⚠️  No requirements.txt found, skipping dependency installation"
fi

echo ""
echo "🔧 Starting development server..."
echo "   You can also run: python3 dev-server.py"
echo ""

# Start the development server
python3 dev-server.py