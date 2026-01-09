"""Vercel serverless function entry point for FastAPI app."""
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

# Export the FastAPI app directly - Vercel's Python runtime handles ASGI apps
__app__ = app

