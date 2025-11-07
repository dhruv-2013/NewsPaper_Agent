"""RAG-based chatbot for querying news highlights."""
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import config
from models import Highlight, ChatMessage
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client (only if enabled and API key provided)
openai_client = None
if config.USE_OPENAI and config.OPENAI_API_KEY:
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    logger.info("OpenAI client initialized for chatbot")
else:
    if not config.USE_OPENAI:
        logger.info("OpenAI disabled in config. Chatbot will use fallback responses.")
    else:
        logger.info("OpenAI API key not provided. Chatbot will use fallback responses.")


class RAGChatbot:
    """RAG-based chatbot for news highlights."""
    
    def __init__(self):
        logger.info("Initializing RAG chatbot...")
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=config.VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="news_highlights",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("RAG chatbot initialized")
    
    def index_highlights(self, highlights: List[Highlight]):
        """Index highlights in the vector database."""
        if not highlights:
            return
        
        logger.info(f"Indexing {len(highlights)} highlights...")
        
        # Clear existing data
        try:
            # Delete all existing entries in the collection
            self.collection.delete(where={})
        except Exception as e:
            logger.warning(f"Could not clear existing highlights index: {e}")
        
        # Prepare documents for indexing
        documents = []
        metadatas = []
        ids = []
        
        for idx, highlight in enumerate(highlights):
            # Create document text
            doc_text = f"""
            Title: {highlight.title}
            Category: {highlight.category}
            Summary: {highlight.summary}
            Sources: {', '.join(highlight.sources)}
            Frequency: {highlight.frequency}
            Keywords: {', '.join(highlight.keywords)}
            """
            
            documents.append(doc_text)
            metadatas.append({
                "title": highlight.title,
                "category": highlight.category,
                "summary": highlight.summary,
                "sources": str(highlight.sources),
                "frequency": str(highlight.frequency),
                "urls": str(highlight.urls)
            })
            ids.append(f"highlight_{idx}")
        
        # Compute embeddings for the documents
        logger.info("Embedding highlights for RAG index...")
        embeddings = self.embedding_model.encode(documents, show_progress_bar=False)

        # Add to collection
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=[embedding.tolist() for embedding in embeddings]
        )
        
        logger.info("Highlights indexed successfully")
    
    def query(self, user_message: str, top_k: int = 3) -> str:
        """Query the chatbot and get a response using RAG."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([user_message])[0].tolist()
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Extract relevant context
            context_docs = results['documents'][0] if results['documents'] else []
            context_metadata = results['metadatas'][0] if results['metadatas'] else []
            
            if not context_docs:
                return "I don't have enough information about recent news highlights to answer your question. Please try asking about sports, lifestyle, music, or finance news."
            
            # Build context for LLM
            context = "\n\n".join([
                f"News Highlight {i+1}:\n{doc}"
                for i, doc in enumerate(context_docs)
            ])
            
            # Generate response using OpenAI
            if openai_client:
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant that answers questions about news highlights. Use the provided context to answer questions accurately. If the context doesn't contain relevant information, say so."
                            },
                            {
                                "role": "user",
                                "content": f"Context from news highlights:\n\n{context}\n\n\nUser question: {user_message}\n\nPlease provide a helpful answer based on the context above."
                            }
                        ],
                        max_tokens=300,
                        temperature=0.7
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    error_str = str(e)
                    # Check for quota/rate limit errors
                    if '429' in error_str or 'quota' in error_str.lower() or 'insufficient_quota' in error_str.lower():
                        logger.warning("OpenAI quota exceeded for chatbot. Using fallback response.")
                        # Fallback: return relevant context
                        return self._generate_fallback_response(context_docs, user_message)
                    else:
                        logger.error(f"Error in chatbot OpenAI call: {str(e)}")
                        return self._generate_fallback_response(context_docs, user_message)
            # Either OpenAI is disabled or we fallback explicitly
            return self._generate_fallback_response(context_docs, user_message)
        except Exception as e:
            logger.error(f"Error in chatbot query: {str(e)}")
            return "I encountered an error while processing your question. Please try again later."
    
    def _generate_fallback_response(self, context_docs: List[str], user_message: str) -> str:
        """Generate a fallback response when OpenAI is unavailable."""
        if not context_docs:
            return "I don't have enough information about recent news highlights to answer your question. Please try asking about sports, lifestyle, music, or finance news."
        
        # Simple keyword matching fallback
        user_lower = user_message.lower()
        relevant_doc = context_docs[0]
        
        # Try to find most relevant doc
        for doc in context_docs:
            if any(word in doc.lower() for word in user_lower.split() if len(word) > 3):
                relevant_doc = doc
                break
        
        # Extract key information
        lines = relevant_doc.split('\n')
        summary = ""
        for line in lines:
            if 'Summary:' in line or 'Title:' in line:
                summary += line + "\n"
        
        if summary:
            return f"Based on the news highlights:\n\n{summary[:400]}..."
        else:
            return f"Based on the news highlights:\n\n{relevant_doc[:400]}..."

