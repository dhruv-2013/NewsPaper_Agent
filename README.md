# AI-Powered News Aggregation & Chatbot

An intelligent news aggregation system that extracts, categorizes, and summarizes news articles from multiple Australian news outlets, with a RAG-based chatbot for interactive queries.

## Features

- **News Extraction**: Automated extraction from Australian news outlets (sports, lifestyle, music, finance)
- **AI Categorization**: Automatic categorization of articles using AI
- **Duplicate Detection**: Identifies similar articles across multiple sources using clustering
- **Smart Highlights**: Generates highlights based on frequency and priority keywords
- **Web Dashboard**: Beautiful, modern UI for viewing daily highlights
- **RAG Chatbot**: Interactive chatbot that answers questions about news highlights using Retrieval-Augmented Generation

## Setup

### 1. Install Dependencies

**Recommended: Use a virtual environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Or use the startup script (handles everything automatically):**
```bash
./run.sh
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
NEWS_API_KEY=your_news_api_key_here
EOF
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY`: Your OpenAI API key (for summarization and chatbot) - **Required for full functionality**
- `NEWS_API_KEY`: Optional, for future News API integration
- `USE_OPENAI`: Set to `false` if you want to disable OpenAI usage and rely on extractive summaries/chatbot fallback (helps conserve credits)

**Note**: The system will work without OpenAI API key but with limited functionality (basic summarization fallback).

### 3. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

### Extracting News

1. Click **"Extract News Now"** button on the dashboard
2. The system will:
   - Extract articles from configured Australian news sources
   - Categorize articles automatically
   - Detect duplicates
   - Generate summaries
   - Create highlights based on frequency and keywords

### Viewing Highlights

Highlights are automatically displayed on the dashboard, organized by category:
- **Sports**
- **Lifestyle**
- **Music**
- **Finance**

Each highlight shows:
- Title and summary
- Frequency (how many sources reported it)
- Priority badge (if it contains breaking news keywords)
- Source information
- Author information

### Using the Chatbot

Ask questions about the news highlights:
- "What are the top sports news?"
- "Tell me about breaking news in finance"
- "What's happening in music?"
- "Summarize the lifestyle highlights"

The chatbot uses RAG (Retrieval-Augmented Generation) to provide accurate answers based on the indexed highlights.

## API Endpoints

### `POST /api/extract`
Trigger news extraction pipeline.

**Request:**
```json
{
  "categories": ["sports", "finance"],  // Optional, null for all
  "force_refresh": true
}
```

### `GET /api/highlights`
Get news highlights.

**Query Parameters:**
- `category`: Optional category filter
- `limit`: Number of highlights (default: 20)

### `GET /api/articles`
Get news articles.

**Query Parameters:**
- `category`: Optional category filter

### `POST /api/chat`
Chat with the RAG chatbot.

**Request:**
```json
{
  "message": "What are the top sports news?"
}
```

### `GET /api/status`
Get system status and statistics.

## Architecture

### Components

1. **News Extractor** (`news_extractor.py`)
   - Web scraping from Australian news outlets
   - Content extraction and parsing

2. **AI Processor** (`ai_processor.py`)
   - Article categorization
   - Summarization using OpenAI
   - Duplicate detection using embeddings and clustering

3. **Database** (`database.py`)
   - SQLite storage for articles and highlights
   - Efficient querying and retrieval

4. **RAG Chatbot** (`rag_chatbot.py`)
   - Vector database (ChromaDB) for semantic search
   - OpenAI integration for response generation

5. **API Server** (`main.py`)
   - FastAPI backend
   - RESTful API endpoints
   - Background task processing

### Data Flow

1. **Extraction** → Articles extracted from news sources
2. **Categorization** → Articles categorized by AI
3. **Summarization** → Summaries generated
4. **Duplicate Detection** → Similar articles grouped
5. **Highlight Generation** → Highlights created based on frequency and keywords
6. **Indexing** → Highlights indexed in vector database for RAG
7. **Display** → Highlights shown in dashboard

## Configuration

Edit `config.py` to customize:
- News sources and categories
- Priority keywords
- Similarity thresholds
- Model settings

## Technologies

- **FastAPI**: Web framework
- **BeautifulSoup**: Web scraping
- **Sentence Transformers**: Embeddings for similarity
- **OpenAI GPT**: Summarization and chatbot
- **ChromaDB**: Vector database for RAG
- **SQLite**: Article storage
- **scikit-learn**: Clustering for duplicate detection

## Notes

- News extraction respects rate limits with delays between requests
- The system processes news extraction in the background
- Duplicate detection uses cosine similarity with configurable threshold
- Highlights are prioritized by frequency and keyword matching
- The chatbot requires OpenAI API key for full functionality

## License

MIT License

