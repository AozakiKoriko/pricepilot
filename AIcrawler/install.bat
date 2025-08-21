@echo off
echo Installing AI Product Aggregation Crawler...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required but not installed.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python is installed.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy env.example .env
    echo Please edit .env file with your API keys before running the application.
) else (
    echo .env file already exists.
)

echo.
echo Installation completed!
echo.
echo To start the application:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Edit .env file with your API keys
echo 3. Run: python run.py
echo.
echo To run tests:
echo python test_crawler.py
echo.
echo To access the API documentation:
echo Start the app and visit: http://localhost:8000/docs
echo.
pause

