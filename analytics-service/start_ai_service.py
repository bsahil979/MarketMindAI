#!/usr/bin/env python
"""Start AI service with correct model configuration"""
import uvicorn
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run("app.ai.ai_api:app", host="0.0.0.0", port=8001, log_level="info")
