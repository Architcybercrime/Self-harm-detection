@echo off
REM Production startup script for Windows
REM Usage: start-production.bat

echo.
echo ============================================
echo 🚀 SafeSignal Production Startup
echo ============================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo Please copy .env.example to .env and fill in values
    pause
    exit /b 1
)

echo ✅ Environment file found

REM Install/update dependencies
echo 📦 Installing dependencies...
cd backend
python -m pip install --upgrade pip setuptools wheel > nul 2>&1
python -m pip install -r requirements.txt > nul 2>&1

echo ✅ Dependencies installed

REM Run tests
echo 🧪 Running tests...
python -m pytest -q --tb=short

if errorlevel 1 (
    echo ❌ Tests failed!
    pause
    exit /b 1
)

echo ✅ All tests passed
echo.

REM Start production server
echo 🌐 Starting Gunicorn server on port 5000...
echo    Backend: http://localhost:5000
echo    Docs: http://localhost:5000/apidocs
echo.
echo Press Ctrl+C to stop
echo.

python -m gunicorn ^
    --worker-class eventlet ^
    -w 1 ^
    --bind 0.0.0.0:5000 ^
    --timeout 300 ^
    --access-logfile - ^
    --error-logfile - ^
    --log-level info ^
    wsgi:app

pause
