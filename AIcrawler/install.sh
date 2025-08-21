#!/bin/bash

echo "Installing AI Product Aggregation Crawler..."

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
if [ -z "$python_version" ]; then
    echo "Error: Python 3.8+ is required but not installed."
    exit 1
fi

echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp env.example .env
    echo "Please edit .env file with your API keys before running the application."
else
    echo ".env file already exists."
fi

echo ""
echo "Installation completed!"
echo ""
echo "To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Edit .env file with your API keys"
echo "3. Run: python run.py"
echo ""
echo "To run tests:"
echo "python test_crawler.py"
echo ""
echo "To access the API documentation:"
echo "Start the app and visit: http://localhost:8000/docs"

