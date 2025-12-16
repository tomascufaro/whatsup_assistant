# WhatsApp Assistant

An AI-powered WhatsApp assistant that helps manage calendars, emails, and client information.

## Features

- WhatsApp integration via Twilio/Meta API
- Google Calendar management
- Email handling via Gmail
- Client database (CSV-based for MVP)
- AI-powered conversation handling using OpenAI/LangChain

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
   - Copy `.env` and fill in your API keys
   - Add OpenAI API key
   - Configure Google OAuth credentials
   - Set up Twilio/Meta WhatsApp credentials

3. Run the application:
```bash
python src/main.py
```

## Project Structure

- `src/main.py` - FastAPI entry point for webhook handling
- `src/agent/` - Core LLM logic and prompts
- `src/tools/` - Calendar, email, and database tools
- `src/services/` - WhatsApp service integration
- `data/` - Local CSV database for clients
- `tests/` - Test files for tools

## Development

Run tests:
```bash
pytest tests/
```

