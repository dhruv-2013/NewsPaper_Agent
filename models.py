"""Data models for the news aggregation system."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Article(BaseModel):
    """Represents a single news article."""
    title: str
    content: str
    author: Optional[str] = None
    source: str
    url: str
    category: Optional[str] = None
    published_date: Optional[datetime] = None
    extracted_at: datetime = Field(default_factory=datetime.now)
    summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    is_duplicate: bool = False
    duplicate_group_id: Optional[str] = None


class Highlight(BaseModel):
    """Represents a news highlight."""
    title: str
    summary: str
    category: str
    sources: List[str] = Field(default_factory=list)
    authors: List[str] = Field(default_factory=list)
    frequency: int = 1
    priority_score: float = 0.0
    keywords: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    published_dates: List[datetime] = Field(default_factory=list)


class ChatMessage(BaseModel):
    """Represents a chat message."""
    message: str
    response: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class NewsExtractionRequest(BaseModel):
    """Request model for triggering news extraction."""
    categories: Optional[List[str]] = None  # If None, extract all categories
    force_refresh: bool = False

