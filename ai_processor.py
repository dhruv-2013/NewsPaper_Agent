"""AI processing module for categorization, summarization, and duplicate detection."""
import logging
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from models import Article, Highlight
import config
from openai import OpenAI
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client (only if enabled and API key provided)
openai_client = None
if config.USE_OPENAI and config.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    logger.info("OpenAI client initialized")
else:
    if not config.USE_OPENAI:
        logger.info("OpenAI disabled in config. Using extractive summarization only.")
    else:
        logger.info("OpenAI API key not provided. Using extractive summarization only.")

# Global flag to track if OpenAI quota is exceeded (to avoid repeated failed calls)
_openai_quota_exceeded = False


class AIProcessor:
    """Handles AI-powered processing of news articles."""
    
    def __init__(self):
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("Embedding model loaded")
    
    def categorize_article(self, article: Article) -> str:
        """Categorize an article using AI."""
        # Use content and title to determine category
        text = f"{article.title} {article.content[:500]}"
        
        # Simple keyword-based categorization (can be enhanced with LLM)
        text_lower = text.lower()
        
        category_scores = {
            "sports": self._score_category(text_lower, [
                "sport", "football", "cricket", "rugby", "tennis", "olympics",
                "athlete", "match", "game", "team", "player", "coach"
            ]),
            "lifestyle": self._score_category(text_lower, [
                "lifestyle", "health", "wellness", "fitness", "diet", "travel",
                "fashion", "beauty", "home", "family", "relationship"
            ]),
            "music": self._score_category(text_lower, [
                "music", "song", "album", "artist", "concert", "festival",
                "musician", "band", "singer", "performance", "chart"
            ]),
            "finance": self._score_category(text_lower, [
                "finance", "business", "economy", "market", "stock", "investment",
                "bank", "money", "dollar", "profit", "revenue", "financial"
            ])
        }
        
        # Return category with highest score
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
        return best_category if category_scores[best_category] > 0 else "lifestyle"
    
    def _score_category(self, text: str, keywords: List[str]) -> float:
        """Score how well text matches a category."""
        score = sum(1 for keyword in keywords if keyword in text)
        return score / len(keywords) if keywords else 0
    
    def summarize_article(self, article: Article) -> str:
        """Generate a summary of an article using AI."""
        global _openai_quota_exceeded
        
        # Check if we should skip OpenAI (quota exceeded or not available)
        if not openai_client or _openai_quota_exceeded:
            return self._extractive_summary(article)
        
        try:
            # Use OpenAI for summarization
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a news summarizer. Create concise, informative summaries."},
                    {"role": "user", "content": f"Summarize this news article in 2-3 sentences:\n\nTitle: {article.title}\n\nContent: {article.content[:2000]}"}
                ],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e)
            # Check for quota/rate limit errors
            if '429' in error_str or 'quota' in error_str.lower() or 'insufficient_quota' in error_str.lower():
                if not _openai_quota_exceeded:
                    logger.warning("OpenAI quota exceeded or rate limited. Switching to extractive summarization for all articles.")
                    _openai_quota_exceeded = True
                # Use extractive summary immediately
                return self._extractive_summary(article)
            else:
                logger.error(f"Error summarizing article: {str(e)}")
                # Fallback to extractive summary
                return self._extractive_summary(article)
    
    def _extractive_summary(self, article: Article) -> str:
        """Create an extractive summary from article content."""
        # Get first few sentences that are substantial
        sentences = [s.strip() for s in article.content.split('.') if len(s.strip()) > 20]
        
        if len(sentences) >= 3:
            # Take first 2-3 sentences
            summary = '. '.join(sentences[:3]) + '.'
        elif len(sentences) >= 2:
            summary = '. '.join(sentences[:2]) + '.'
        elif len(sentences) >= 1:
            summary = sentences[0] + '.'
        else:
            # Fallback to first 200 chars
            summary = article.content[:200]
            if len(article.content) > 200:
                summary += '...'
        
        # Ensure summary is not too long
        if len(summary) > 300:
            summary = summary[:300] + '...'
        
        return summary
    
    def detect_duplicates(self, articles: List[Article]) -> List[Article]:
        """Detect duplicate or similar articles using clustering."""
        if len(articles) < 2:
            return articles
        
        logger.info(f"Detecting duplicates among {len(articles)} articles...")
        
        try:
            # Create embeddings for all articles
            texts = [f"{article.title} {article.content[:500]}" for article in articles]
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(embeddings)
            
            # Use DBSCAN clustering to find similar articles
            # Convert similarity to distance and ensure non-negative
            distance_matrix = 1 - similarity_matrix
            # Clip to ensure non-negative (handle floating point precision issues)
            distance_matrix = np.clip(distance_matrix, 0, None)
            # Ensure diagonal is zero (distance to self)
            np.fill_diagonal(distance_matrix, 0)
            
            # Use DBSCAN with eps based on similarity threshold
            eps = 1 - config.SIMILARITY_THRESHOLD
            clustering = DBSCAN(eps=eps, min_samples=2, metric='precomputed')
            cluster_labels = clustering.fit_predict(distance_matrix)
        except Exception as e:
            logger.error(f"Error in duplicate detection: {str(e)}")
            # Return articles without duplicate detection if clustering fails
            return articles
        
        # Group articles by cluster
        cluster_groups = {}
        for idx, label in enumerate(cluster_labels):
            if label != -1:  # -1 means noise (no cluster)
                if label not in cluster_groups:
                    cluster_groups[label] = []
                cluster_groups[label].append(idx)
        
        # Mark duplicates
        processed_articles = articles.copy()
        for cluster_id, indices in cluster_groups.items():
            # Keep the first article as primary, mark others as duplicates
            primary_idx = indices[0]
            for dup_idx in indices[1:]:
                processed_articles[dup_idx].is_duplicate = True
                processed_articles[dup_idx].duplicate_group_id = f"group_{cluster_id}"
                processed_articles[primary_idx].duplicate_group_id = f"group_{cluster_id}"
        
        logger.info(f"Found {len(cluster_groups)} duplicate groups")
        return processed_articles
    
    def generate_highlights(
        self, 
        articles: List[Article], 
        category: str
    ) -> List[Highlight]:
        """Generate highlights for a category based on frequency and keywords."""
        # Filter articles by category and remove duplicates
        category_articles = [
            a for a in articles 
            if a.category == category and not a.is_duplicate
        ]
        
        if not category_articles:
            return []
        
        # Group similar articles (already grouped by duplicate detection)
        article_groups = {}
        for article in category_articles:
            group_id = article.duplicate_group_id or f"single_{article.url}"
            if group_id not in article_groups:
                article_groups[group_id] = []
            article_groups[group_id].append(article)
        
        highlights = []
        for group_id, group_articles in article_groups.items():
            # Calculate priority score
            frequency = len(group_articles)
            
            # Check for priority keywords
            priority_score = 0.0
            all_text = ' '.join([f"{a.title} {a.content[:200]}" for a in group_articles]).lower()
            
            for keyword in config.PRIORITY_KEYWORDS:
                if keyword in all_text:
                    priority_score += 1.0
            
            # Boost score for high frequency
            priority_score += frequency * 0.5
            
            # Create highlight
            primary_article = group_articles[0]
            
            # Generate or use existing summary
            summary = primary_article.summary
            if not summary:
                summary = self.summarize_article(primary_article)
            
            highlight = Highlight(
                title=primary_article.title,
                summary=summary,
                category=category,
                sources=[a.source for a in group_articles],
                authors=[a.author for a in group_articles if a.author],
                frequency=frequency,
                priority_score=priority_score,
                keywords=config.PRIORITY_KEYWORDS if priority_score > 0 else [],
                urls=[a.url for a in group_articles],
                published_dates=[a.published_date for a in group_articles if a.published_date]
            )
            
            highlights.append(highlight)
        
        # Sort by priority score and frequency
        highlights.sort(key=lambda x: (x.priority_score, x.frequency), reverse=True)
        
        return highlights

