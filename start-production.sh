#!/bin/bash
# Production startup script for local testing
# Usage: bash start-production.sh

set -e

echo "🚀 SafeSignal Production Startup"
echo "================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and fill in values"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '#' | xargs)

# Verify critical variables
if [ -z "$JWT_SECRET_KEY" ]; then
    echo "❌ JWT_SECRET_KEY not set in .env"
    exit 1
fi

if [ -z "$SUPABASE_URL" ]; then
    echo "⚠️  SUPABASE_URL not set - using mock mode (development only)"
fi

echo "✅ Environment configured"

# Install/update dependencies
echo "📦 Installing dependencies..."
cd backend
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Run tests
echo "🧪 Running tests..."
python -m pytest -q --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ All tests passed"

# Start production server
echo "🌐 Starting Gunicorn server on port 5000..."
echo "   Backend: http://localhost:5000"
echo "   Docs: http://localhost:5000/apidocs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

gunicorn \
    --worker-class eventlet \
    -w 1 \
    --bind 0.0.0.0:5000 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:app

