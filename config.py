"""Configuration settings for the news aggregation system."""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# OpenAI Settings
# Set to False to disable OpenAI and use extractive summarization only (saves credits)
USE_OPENAI = os.getenv("USE_OPENAI", "true").lower() == "true"

# News Sources - Australian News Outlets
NEWS_SOURCES = {
    "sports": [
        "https://www.abc.net.au/news/sport/",
        "https://www.smh.com.au/sport",
        "https://www.theage.com.au/sport",
    ],
    "lifestyle": [
        "https://www.abc.net.au/news/lifestyle/",
        "https://www.smh.com.au/lifestyle",
        "https://www.theage.com.au/lifestyle",
    ],
    "music": [
        "https://www.abc.net.au/news/entertainment/arts/",
        "https://www.smh.com.au/entertainment/music",
    ],
    "finance": [
        "https://www.abc.net.au/news/business/",
        "https://www.smh.com.au/business",
        "https://www.theage.com.au/business",
        "https://www.afr.com/",
    ],
}

# Categories
CATEGORIES = ["sports", "lifestyle", "music", "finance"]

# Keywords for priority highlights
PRIORITY_KEYWORDS = [
    "breaking news",
    "breaking",
    "urgent",
    "exclusive",
    "alert",
    "update",
    "developing",
]

# Model settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.85  # For duplicate detection

# Database
DATABASE_PATH = "news_data.db"
VECTOR_DB_PATH = "chroma_db"

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000

