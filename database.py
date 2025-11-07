"""Database module for storing news articles and highlights."""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from models import Article, Highlight
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsDatabase:
    """Database handler for news articles and highlights."""
    
    def __init__(self, db_path: str = "news_data.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT,
                source TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                category TEXT,
                published_date TEXT,
                extracted_at TEXT NOT NULL,
                summary TEXT,
                keywords TEXT,
                is_duplicate INTEGER DEFAULT 0,
                duplicate_group_id TEXT
            )
        ''')
        
        # Highlights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                category TEXT NOT NULL,
                sources TEXT NOT NULL,
                authors TEXT,
                frequency INTEGER DEFAULT 1,
                priority_score REAL DEFAULT 0.0,
                keywords TEXT,
                urls TEXT NOT NULL,
                published_dates TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def save_articles(self, articles: List[Article]):
        """Save articles to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (title, content, author, source, url, category, published_date,
                     extracted_at, summary, keywords, is_duplicate, duplicate_group_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.title,
                    article.content,
                    article.author,
                    article.source,
                    article.url,
                    article.category,
                    article.published_date.isoformat() if article.published_date else None,
                    article.extracted_at.isoformat(),
                    article.summary,
                    json.dumps(article.keywords),
                    1 if article.is_duplicate else 0,
                    article.duplicate_group_id
                ))
            except Exception as e:
                logger.error(f"Error saving article {article.url}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(articles)} articles to database")
    
    def get_articles(self, category: Optional[str] = None) -> List[Article]:
        """Retrieve articles from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('SELECT * FROM articles WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM articles')
        
        rows = cursor.fetchall()
        conn.close()
        
        articles = []
        for row in rows:
            try:
                article = Article(
                    title=row[1],
                    content=row[2],
                    author=row[3],
                    source=row[4],
                    url=row[5],
                    category=row[6],
                    published_date=datetime.fromisoformat(row[7]) if row[7] else None,
                    extracted_at=datetime.fromisoformat(row[8]),
                    summary=row[9],
                    keywords=json.loads(row[10]) if row[10] else [],
                    is_duplicate=bool(row[11]),
                    duplicate_group_id=row[12]
                )
                articles.append(article)
            except Exception as e:
                logger.error(f"Error loading article: {str(e)}")
                continue
        
        return articles
    
    def save_highlights(self, highlights: List[Highlight]):
        """Save highlights to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear old highlights
        cursor.execute('DELETE FROM highlights')
        
        for highlight in highlights:
            try:
                cursor.execute('''
                    INSERT INTO highlights 
                    (title, summary, category, sources, authors, frequency,
                     priority_score, keywords, urls, published_dates, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    highlight.title,
                    highlight.summary,
                    highlight.category,
                    json.dumps(highlight.sources),
                    json.dumps(highlight.authors),
                    highlight.frequency,
                    highlight.priority_score,
                    json.dumps(highlight.keywords),
                    json.dumps(highlight.urls),
                    json.dumps([d.isoformat() for d in highlight.published_dates if d]),
                    datetime.now().isoformat()
                ))
            except Exception as e:
                logger.error(f"Error saving highlight: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(highlights)} highlights to database")
    
    def get_highlights(self, category: Optional[str] = None, limit: int = 20) -> List[Highlight]:
        """Retrieve highlights from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM highlights 
                WHERE category = ? 
                ORDER BY priority_score DESC, frequency DESC 
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT * FROM highlights 
                ORDER BY priority_score DESC, frequency DESC 
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        highlights = []
        for row in rows:
            try:
                highlight = Highlight(
                    title=row[1],
                    summary=row[2],
                    category=row[3],
                    sources=json.loads(row[4]),
                    authors=json.loads(row[5]) if row[5] else [],
                    frequency=row[6],
                    priority_score=row[7],
                    keywords=json.loads(row[8]) if row[8] else [],
                    urls=json.loads(row[9]),
                    published_dates=[
                        datetime.fromisoformat(d) for d in json.loads(row[10]) if d
                    ] if row[10] else []
                )
                highlights.append(highlight)
            except Exception as e:
                logger.error(f"Error loading highlight: {str(e)}")
                continue
        
        return highlights

