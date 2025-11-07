"""News extraction module for Australian news outlets."""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
from datetime import datetime
import re
from urllib.parse import urljoin
from dateutil import parser
from models import Article
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsExtractor:
    """Extracts news articles from Australian news outlets."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def extract_articles(self, category: str, sources: List[str]) -> List[Article]:
        """Extract articles from given sources for a category."""
        articles = []
        
        for source_url in sources:
            try:
                logger.info(f"Extracting from {source_url} for category {category}")
                articles_from_source = self._extract_from_source(source_url, category)
                articles.extend(articles_from_source)
                time.sleep(1)  # Be respectful with requests
            except Exception as e:
                logger.error(f"Error extracting from {source_url}: {str(e)}")
                continue
        
        return articles
    
    def _extract_from_source(self, url: str, category: str) -> List[Article]:
        """Extract articles from a single source."""
        articles = []
        
        try:
            logger.info(f"Fetching {url}...")
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common patterns for news article links
            article_links = []
            seen_urls = set()
            
            # Find article links (common patterns)
            # Try multiple strategies
            link_selectors = [
                'a[href*="/news/"]',
                'a[href*="/article/"]',
                'a[href*="/story/"]',
                'a[href*="/sport/"]',
                'a[href*="/business/"]',
                'a[href*="/lifestyle/"]',
                'a[href*="/entertainment/"]',
                'article a',
                '.article a',
                '.story a',
                '.news-item a',
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    if href and text and len(text) > 20:
                        full_url = self._make_absolute_url(url, href)
                        if full_url not in seen_urls and self._is_article_link(href, text):
                            article_links.append((full_url, text))
                            seen_urls.add(full_url)
            
            # Fallback: find all links and filter
            if not article_links:
                logger.warning(f"No articles found with selectors, trying fallback for {url}")
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if href and text and len(text) > 20:
                        full_url = self._make_absolute_url(url, href)
                        if full_url not in seen_urls and self._is_article_link(href, text):
                            article_links.append((full_url, text))
                            seen_urls.add(full_url)
            
            logger.info(f"Found {len(article_links)} potential articles from {url}")
            
            # Extract content from each article (limit to avoid too many requests)
            max_articles = min(10, len(article_links))
            for idx, (article_url, title) in enumerate(article_links[:max_articles]):
                try:
                    logger.debug(f"Extracting article {idx+1}/{max_articles}: {title[:50]}...")
                    article = self._extract_article_content(article_url, title, url, category)
                    if article:
                        articles.append(article)
                        logger.debug(f"Successfully extracted article: {article.title[:50]}")
                    time.sleep(0.5)  # Be respectful
                except Exception as e:
                    logger.warning(f"Error extracting article {article_url}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(articles)} articles from {url}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error processing {url}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
        
        return articles
    
    def _is_article_link(self, href: str, text: str) -> bool:
        """Determine if a link is likely an article."""
        if not text or len(text) < 20:
            return False
        
        # Exclude common non-article links
        exclude_patterns = [
            '/tag/', '/category/', '/author/', '/page/', '/search',
            'mailto:', 'javascript:', '#', '/about', '/contact'
        ]
        
        for pattern in exclude_patterns:
            if pattern in href.lower():
                return False
        
        # Include patterns that suggest articles
        include_patterns = [
            '/news/', '/article/', '/story/', '/2024/', '/2023/',
            '/sport/', '/lifestyle/', '/business/', '/entertainment/'
        ]
        
        return any(pattern in href.lower() for pattern in include_patterns)
    
    def _make_absolute_url(self, base_url: str, href: str) -> str:
        """Convert relative URL to absolute."""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return urljoin(base_url, href)
        else:
            return f"{base_url.rstrip('/')}/{href}"
    
    def _extract_article_content(self, url: str, title: str, source: str, category: str) -> Article:
        """Extract full content from an article URL."""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            content = ""
            
            # Try common article content selectors (more comprehensive)
            content_selectors = [
                'article',
                '.article-body',
                '.story-body',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                '[role="article"]',
                'main article',
                '.main-content',
                '#article-body',
                '#content',
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script, style, and other non-content elements
                    for element in content_elem(["script", "style", "nav", "header", "footer", "aside", ".ad", ".advertisement"]):
                        element.decompose()
                    content = content_elem.get_text(separator=' ', strip=True)
                    if len(content) > 200:  # Ensure we got substantial content
                        break
            
            # Fallback: get all paragraph text from main content areas
            if not content or len(content) < 200:
                # Try to find main content area first
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|article|story', re.I))
                if main_content:
                    paragraphs = main_content.find_all('p')
                else:
                    paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Extract author
            author = None
            author_selectors = [
                '.author', '.byline', '[rel="author"]', '.writer'
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Extract published date
            published_date = None
            date_selectors = [
                'time', '.published-date', '.date', '[datetime]'
            ]
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    if date_str:
                        try:
                            published_date = parser.parse(date_str)
                        except:
                            pass
                    break
            
            # Clean content
            content = re.sub(r'\s+', ' ', content).strip()
            
            if len(content) < 100:  # Skip articles with too little content
                return None
            
            return Article(
                title=title[:500],  # Limit title length
                content=content[:5000],  # Limit content length
                author=author,
                source=source,
                url=url,
                category=category,
                published_date=published_date
            )
        
        except Exception as e:
            logger.warning(f"Error extracting content from {url}: {str(e)}")
            return None

