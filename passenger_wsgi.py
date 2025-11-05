"""
Passenger WSGI Configuration for Addi Backend
DreamHost Shared Hosting with Phusion Passenger 6.0.10
Python 3.10.12
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up environment - load .env file if it exists
from pathlib import Path
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

# Import the FastAPI application
from main import app

# Passenger expects an 'application' callable
application = app

