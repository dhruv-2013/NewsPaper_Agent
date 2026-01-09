# Deployment Guide

This application can be deployed on various platforms:

## Quick Deploy Options

### Railway
1. Connect your GitHub repository
2. Railway will auto-detect Python and install dependencies
3. Set environment variables:
   - `OPENAI_API_KEY` (required)
   - `USE_OPENAI=true` (optional)
4. Deploy!

### Render
1. Create a new Web Service
2. Connect your GitHub repository
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables in dashboard
6. Deploy!

### Fly.io
1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Run: `fly launch`
3. Set secrets: `fly secrets set OPENAI_API_KEY=your_key`
4. Deploy: `fly deploy`

### Heroku
1. Install Heroku CLI
2. Run: `heroku create`
3. Set config: `heroku config:set OPENAI_API_KEY=your_key`
4. Deploy: `git push heroku main`

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required for full functionality)
- `USE_OPENAI` - Set to `false` to disable OpenAI (uses fallback summaries)
- `PORT` - Server port (auto-set by most platforms)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py

# Or with uvicorn
uvicorn main:app --reload
```

