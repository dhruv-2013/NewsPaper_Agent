"""Vercel serverless function entry point for FastAPI app."""
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

# Export handler for Vercel - the app will be used as the handler
handler = app

