"""Main FastAPI application for news aggregation system."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from typing import List, Optional
import logging
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware

from models import Article, Highlight, ChatMessage, NewsExtractionRequest
from news_extractor import NewsExtractor
from ai_processor import AIProcessor
from database import NewsDatabase
from rag_chatbot import RAGChatbot
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI-Powered News Aggregation System")

# Add CSP headers middleware (permissive for development)
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Set Content Security Policy that allows inline scripts and eval for development
        # Note: In production, you may want to restrict this further
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        return response

app.add_middleware(CSPMiddleware)

# Initialize components
extractor = NewsExtractor()
ai_processor = AIProcessor()
database = NewsDatabase()
chatbot = RAGChatbot()

# Templates
templates = Jinja2Templates(directory="templates")


def process_news_pipeline(categories: Optional[List[str]] = None):
    """Process news extraction, categorization, and highlight generation."""
    try:
        logger.info("Starting news processing pipeline...")
        
        if categories is None:
            categories = config.CATEGORIES
        
        all_articles = []
        
        # Extract articles for each category
        for category in categories:
            if category not in config.NEWS_SOURCES:
                logger.warning(f"Category {category} not found in NEWS_SOURCES")
                continue
            
            sources = config.NEWS_SOURCES[category]
            logger.info(f"Extracting {category} news from {len(sources)} sources...")
            articles = extractor.extract_articles(category, sources)
            logger.info(f"Extracted {len(articles)} articles for {category}")
            
            if not articles:
                logger.warning(f"No articles extracted for category {category}")
                continue
            
            # Categorize articles
            logger.info(f"Categorizing and summarizing {len(articles)} articles for {category}...")
            for idx, article in enumerate(articles):
                try:
                    if not article.category:
                        article.category = ai_processor.categorize_article(article)
                    article.summary = ai_processor.summarize_article(article)
                    if (idx + 1) % 5 == 0:
                        logger.info(f"Processed {idx + 1}/{len(articles)} articles for {category}")
                except Exception as e:
                    logger.error(f"Error processing article {idx} in {category}: {str(e)}")
                    continue
            
            all_articles.extend(articles)
            logger.info(f"Total articles so far: {len(all_articles)}")
        
        if not all_articles:
            logger.error("No articles extracted from any source!")
            return {"status": "error", "message": "No articles extracted", "articles_count": 0, "highlights_count": 0}
        
        logger.info(f"Total articles extracted: {len(all_articles)}")
        
        # Detect duplicates
        logger.info("Detecting duplicates...")
        all_articles = ai_processor.detect_duplicates(all_articles)
        unique_count = len([a for a in all_articles if not a.is_duplicate])
        logger.info(f"Found {len(all_articles) - unique_count} duplicates, {unique_count} unique articles")
        
        # Save articles
        logger.info("Saving articles to database...")
        database.save_articles(all_articles)
        
        # Generate highlights for each category
        logger.info("Generating highlights...")
        all_highlights = []
        for category in categories:
            highlights = ai_processor.generate_highlights(all_articles, category)
            logger.info(f"Generated {len(highlights)} highlights for {category}")
            all_highlights.extend(highlights)
        
        # Save highlights
        logger.info(f"Saving {len(all_highlights)} highlights to database...")
        database.save_highlights(all_highlights)
        
        # Index highlights for RAG
        logger.info("Indexing highlights for RAG chatbot...")
        chatbot.index_highlights(all_highlights)
        
        logger.info(f"News processing pipeline completed successfully: {len(all_articles)} articles, {len(all_highlights)} highlights")
        return {"status": "success", "articles_count": len(all_articles), "highlights_count": len(all_highlights)}
    
    except Exception as e:
        logger.error(f"Error in news processing pipeline: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e), "articles_count": 0, "highlights_count": 0}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with news highlights dashboard."""
    highlights = database.get_highlights(limit=50)
    
    # Group by category
    highlights_by_category = {}
    for highlight in highlights:
        if highlight.category not in highlights_by_category:
            highlights_by_category[highlight.category] = []
        highlights_by_category[highlight.category].append(highlight)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "highlights_by_category": highlights_by_category,
            "categories": config.CATEGORIES
        }
    )


@app.post("/api/extract")
async def extract_news(
    request: NewsExtractionRequest,
    background_tasks: BackgroundTasks
):
    """Trigger news extraction pipeline."""
    try:
        categories = request.categories or config.CATEGORIES
        
        # Run in background
        background_tasks.add_task(process_news_pipeline, categories)
        
        return {
            "status": "started",
            "message": f"News extraction started for categories: {', '.join(categories)}",
            "categories": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/highlights")
async def get_highlights(category: Optional[str] = None, limit: int = 20):
    """Get news highlights."""
    try:
        highlights = database.get_highlights(category=category, limit=limit)
        return {"highlights": [h.dict() for h in highlights]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articles")
async def get_articles(category: Optional[str] = None):
    """Get news articles."""
    try:
        articles = database.get_articles(category=category)
        return {"articles": [a.dict() for a in articles]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Chat with the RAG chatbot."""
    try:
        response_text = chatbot.query(message.message)
        return {
            "message": message.message,
            "response": response_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """Get system status."""
    try:
        articles_count = len(database.get_articles())
        highlights_count = len(database.get_highlights())
        
        # Get articles by category
        articles_by_category = {}
        for category in config.CATEGORIES:
            articles_by_category[category] = len([a for a in database.get_articles() if a.category == category])
        
        return {
            "status": "operational",
            "articles_count": articles_count,
            "highlights_count": highlights_count,
            "articles_by_category": articles_by_category,
            "categories": config.CATEGORIES
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)

