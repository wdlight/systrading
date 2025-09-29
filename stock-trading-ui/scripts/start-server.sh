#!/bin/bash

# Frontend Development Server Startup Script
# This script ensures only one development server runs on port 9000

set -e

echo "🚀 Starting Frontend Development Server..."

# Kill any existing Next.js development servers
echo "🔄 Checking for existing development servers..."
if pgrep -f "next dev" > /dev/null; then
    echo "⏹️  Stopping existing Next.js development servers..."
    pkill -f "next dev" || true
    sleep 2
fi

# Kill any process using port 9000
echo "🔄 Checking port 9000..."
if lsof -ti:9000 > /dev/null 2>&1; then
    echo "⏹️  Stopping process on port 9000..."
    lsof -ti:9000 | xargs kill -9 || true
    sleep 1
fi

# Navigate to project directory
cd "$(dirname "$0")/.."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start development server on port 9000
echo "🌐 Starting development server on http://localhost:9000"
echo "📊 Test Chart Page: http://localhost:9000/test-chart"
echo "📈 Korean Trading: http://localhost:9000/korean-trading"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm run dev

echo "✅ Development server stopped"
