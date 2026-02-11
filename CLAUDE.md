# Real Estate AI Chatbot — Project Context

## What This Project Does
Multi-platform AI chatbot for Egyptian real estate companies.
- Receives customer messages from WhatsApp, Facebook Messenger, and Instagram DM via Meta webhooks
- Responds intelligently using Claude Haiku 4.5 API based on actual property data
- Automatically qualifies leads (Hot/Warm/Cold) and stores them in database
- Admin panel for the sales team to monitor leads and conversations

## Tech Stack
- **Backend**: Python 3.12 / FastAPI (async everywhere)
- **Database**: PostgreSQL 16 (via async SQLAlchemy 2.0 + Alembic)
- **AI**: Claude Haiku 4.5 — model: `claude-haiku-4-5-20251001` (Anthropic API)
- **Messaging**: Meta Graph API v21.0 (WhatsApp Cloud API + Messenger + Instagram)
- **Admin Panel**: React 18 + Tailwind CSS + Recharts
- **Deployment**: Railway (backend + PostgreSQL + static frontend)

## Critical Business Rules
1. Bot responds in **Arabic (Egyptian dialect)** by default
2. Switches to English ONLY if customer writes in English
3. **NEVER fabricate property data** — only use data from knowledge base
4. If bot doesn't know the answer → say so + offer to connect with sales team
5. Collect from customer: name, phone, preferred project, budget, timeline
6. Lead created after collecting at least name + phone number
7. Lead classification:
   - **Hot** = wants to visit site / ready to book / asks about availability
   - **Warm** = asking detailed questions about prices/payment plans
   - **Cold** = just browsing / vague questions
8. Notify sales team immediately for Hot leads

## Architecture Notes
- ALL three platforms use the SAME Meta App and can share ONE webhook endpoint
- Differentiate platform by checking webhook payload:
  - WhatsApp: `object` = `"whatsapp_business_account"`, messages in `entry[].changes[].value.messages[]`
  - Messenger: `object` = `"page"`, messages in `entry[].messaging[].message`
  - Instagram: `object` = `"instagram"`, messages in `entry[].messaging[].message`
- Webhook MUST return HTTP 200 within 5 seconds — process message in background
- All messaging within 24-hour customer service window is FREE on all 3 platforms
- WhatsApp per-message pricing (July 2025+): service replies = free, templates = paid
- Messenger and Instagram: completely free, no per-message charges
- Instagram API rate limit: 200 calls/hour (sufficient for our use case)

## Coding Standards
- Python type hints on ALL functions
- Pydantic v2 for all data validation and schemas
- async/await for ALL I/O operations (database, HTTP, file)
- Comprehensive error handling with structured JSON logging
- Docstrings on all public functions
- Environment variables for ALL secrets (never hardcode)
- Consistent JSON API response format: `{"success": bool, "data": ..., "error": ...}`
- Tests for all critical paths using pytest + pytest-asyncio

## Project Structure
real-estate-chatbot/
├── CLAUDE.md
├── .env.example
├── .gitignore
├── requirements.txt
├── Procfile                  # Railway deployment
├── railway.json              # Railway config
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app + lifespan
│   ├── config.py              # Pydantic Settings
│   ├── database.py            # Async SQLAlchemy engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py            # Base model with common fields
│   │   ├── lead.py            # Lead model
│   │   ├── conversation.py    # Conversation + Message models
│   │   └── property.py        # Project + Unit models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── webhook.py         # POST /webhook (receive) + GET /webhook (verify)
│   │   ├── admin.py           # /api/admin/* endpoints
│   │   └── health.py          # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── claude_service.py  # Claude API with prompt caching
│   │   ├── meta_service.py    # Send messages to WhatsApp/Messenger/Instagram
│   │   ├── webhook_handler.py # Parse & route incoming webhooks by platform
│   │   ├── lead_service.py    # Lead CRUD + classification
│   │   ├── notification_service.py  # Sales team alerts
│   │   └── knowledge.py       # Load property data → context for Claude
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── webhook.py         # Webhook payload schemas
│   │   ├── lead.py            # Lead request/response schemas
│   │   └── admin.py           # Admin API schemas
│   └── prompts/
│       └── system_prompt.py   # System prompt builder function
├── admin-panel/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js             # API client with auth
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Leads.jsx
│       │   ├── LeadDetail.jsx
│       │   └── Conversations.jsx
│       └── components/
│           ├── Layout.jsx
│           ├── Sidebar.jsx
│           ├── StatsCard.jsx
│           ├── LeadTable.jsx
│           ├── ChatBubble.jsx
│           └── PlatformBadge.jsx
├── data/
│   └── properties.json        # Sample property knowledge base
├── tests/
│   ├── conftest.py
│   ├── test_webhook.py
│   ├── test_claude_service.py
│   ├── test_meta_service.py
│   ├── test_lead_service.py
│   └── test_admin.py
└── scripts/
    └── seed_properties.py     # Load properties into DB
