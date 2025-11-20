@echo off
REM MedEx Backend - Setup Script for Windows

setlocal enabledelayedexpansion

echo ==================================
echo MedEx Backend Setup (Windows)
echo ==================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo OK - Python %PYTHON_VERSION% found
echo.

REM Check MongoDB
echo [2/5] Checking MongoDB...
echo Warning: Ensure MongoDB is running on localhost:27017
echo If not, start it with: docker run -d -p 27017:27017 mongo
echo.

REM Virtual environment
echo [3/5] Setting up virtual environment...
if not exist "venv" (
    echo Creating new virtual environment...
    python -m venv venv
    echo OK - Virtual environment created
) else (
    echo OK - Virtual environment exists
)
echo.

REM Activate and install
echo [4/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
echo OK - Dependencies installed
echo.

REM Check .env
echo [5/5] Checking configuration...
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo OK - .env created
) else (
    echo OK - .env exists
)
echo.

REM Create uploads directory
if not exist "uploads" (
    mkdir uploads
)

echo ==================================
echo OK - Setup complete!
echo ==================================
echo.
echo Starting FastAPI backend...
echo.
echo Server will run at:
echo   http://localhost:8000
echo.
echo API Documentation (Swagger):
echo   http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server
uvicorn server:app --reload --host 0.0.0.0 --port 8000

pause
