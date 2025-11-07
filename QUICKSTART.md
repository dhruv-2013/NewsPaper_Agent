# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (recommended for full functionality)

## Installation Steps

1. **Clone/Navigate to the project directory**
   ```bash
   cd /Users/dhruvgulwani/Desktop/FOBOH
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_key_here" > .env
   echo "NEWS_API_KEY=optional" >> .env
echo "USE_OPENAI=true" >> .env
   ```
   
   Or manually create `.env` file with:
   ```
   OPENAI_API_KEY=sk-...
   NEWS_API_KEY=optional
USE_OPENAI=true
   ```

5. **Run the application**
   ```bash
   python main.py
   ```
   
   Or use the startup script:
   ```bash
   ./run.sh
   ```

6. **Access the dashboard**
   - Open browser: http://localhost:8000
   - Click "Extract News Now" to start gathering news
   - Wait for processing (runs in background)
   - View highlights organized by category
   - Use the chatbot to ask questions about the news

## First Run

1. Start the server
2. Click "Extract News Now" button
3. Wait 1-2 minutes for processing
4. Click "Refresh Highlights" to see results
5. Try asking the chatbot: "What are the top sports news?"

## Troubleshooting

### No highlights showing?
- Make sure news extraction completed
- Check browser console for errors
- Verify API endpoints are working: http://localhost:8000/api/status

### OpenAI API errors?
- Verify your API key is correct in `.env`
- Check you have API credits
- System will work with fallback summarization if API unavailable

### Import errors?
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)

## API Usage Examples

### Extract News
```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"categories": ["sports", "finance"]}'
```

### Get Highlights
```bash
curl http://localhost:8000/api/highlights?category=sports&limit=10
```

### Chat with Bot
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top sports news?"}'
```

## Next Steps

- Customize news sources in `config.py`
- Adjust similarity threshold for duplicate detection
- Modify priority keywords for highlights
- Add more categories as needed

