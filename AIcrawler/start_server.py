#!/usr/bin/env python3
"""
Start script for AIcrawler backend service
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("Starting AIcrawler backend service...")
    print("Service will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("API docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the service")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
