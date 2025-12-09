@echo off
echo ========================================
echo   Token Health Backend Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements_health.txt
echo Dependencies installed.
echo.

REM Start the server
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo ========================================
echo.
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause
