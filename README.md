# Real Estate AI Chatbot

Multi-platform AI chatbot for Egyptian real estate companies. Automatically responds to customer inquiries on WhatsApp, Facebook Messenger, and Instagram DM using Claude AI, qualifies leads, and provides a comprehensive admin dashboard for sales teams.

## Features

- **Multi-Platform Support**: Unified bot handling WhatsApp, Messenger, and Instagram messages
- **AI-Powered Responses**: Claude Haiku 4.5 generates contextual, intelligent replies in Arabic or English
- **Automatic Lead Qualification**: Classifies leads as Hot/Warm/Cold based on conversation analysis
- **Lead Data Extraction**: Automatically extracts customer name, phone, budget, timeline, and interests
- **Real-Time Admin Dashboard**: Monitor leads, conversations, and analytics
- **Instant Notifications**: Sales team alerts for hot leads
- **Property Knowledge Base**: AI responds using actual property data (never fabricates information)
- **Conversation History**: Track full customer journey across all platforms
- **Prompt Caching**: Optimized Claude API usage with ephemeral caching

## Tech Stack

### Backend
- **Python 3.12** with FastAPI (fully async)
- **PostgreSQL 16** via async SQLAlchemy 2.0 + Alembic migrations
- **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`) via Anthropic API
- **Meta Graph API v21.0** for WhatsApp Cloud API, Messenger, and Instagram

### Frontend
- **React 18** with Vite
- **Tailwind CSS** for styling
- **Recharts** for analytics visualizations

### Deployment
- **Railway** (backend + PostgreSQL database + static frontend hosting)

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Meta Business Account with App configured for WhatsApp, Messenger, and Instagram
- Anthropic API key for Claude

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd real-estate-chatbot
```

### 2. Environment Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Fill in your credentials (see [Environment Variables](#environment-variables) section below).

### 3. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Load sample property data
python scripts/seed_properties.py

# Start development server
uvicorn app.main:app --reload
```

Backend will run on `http://localhost:8000`

### 4. Admin Panel Setup

```bash
cd admin-panel

# Install dependencies
npm install

# Start development server
npm run dev
```

Admin panel will run on `http://localhost:5173`

## Meta Platform Setup

### WhatsApp Business API

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app (Business type)
3. Add **WhatsApp Business** product
4. Configure webhook:
   - Callback URL: `https://your-domain.com/webhook`
   - Verify Token: (set in `META_VERIFY_TOKEN` env var)
   - Subscribe to: `messages`
5. Get credentials:
   - Phone Number ID
   - WhatsApp Business Account ID
   - Access Token (temporary → generate permanent token)
6. Add your test phone number to allowed list

### Facebook Messenger

1. In the same Meta App, add **Messenger** product
2. Create/connect a Facebook Page
3. Configure webhook:
   - Same callback URL: `https://your-domain.com/webhook`
   - Subscribe to: `messages`, `messaging_postbacks`
4. Get Page Access Token from Messenger settings

### Instagram Messaging

1. In the same Meta App, add **Instagram** product
2. Connect your Instagram Business Account
3. Configure webhook:
   - Same callback URL: `https://your-domain.com/webhook`
   - Subscribe to: `messages`
4. Get Instagram Access Token

**Important Notes:**
- All three platforms can use the **same webhook endpoint**
- The bot automatically detects platform from payload structure
- Test in Meta's test environment before going live
- WhatsApp requires business verification for production use

## Railway Deployment

### Initial Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize project
railway login
railway init

# Add PostgreSQL database
railway add --database postgresql
```

### Configure Environment Variables

Set these in Railway dashboard (Settings → Variables):

```
DATABASE_URL=(auto-populated by Railway)
ANTHROPIC_API_KEY=your_anthropic_key
META_VERIFY_TOKEN=your_verify_token
WHATSAPP_ACCESS_TOKEN=your_wa_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_waba_id
MESSENGER_PAGE_ACCESS_TOKEN=your_page_token
MESSENGER_PAGE_ID=your_page_id
INSTAGRAM_ACCESS_TOKEN=your_ig_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id
ADMIN_API_KEY=generate_secure_random_key
APP_ENV=production
```

### Deploy

```bash
# Deploy backend
railway up

# Get deployment URL
railway open
```

### Update Meta Webhooks

After deployment, update webhook URLs in Meta App settings to your Railway URL:
- `https://your-railway-app.up.railway.app/webhook`

### Admin Panel Deployment

Admin panel is served as static files from Railway. Build and deploy:

```bash
cd admin-panel
npm run build

# Deploy static files (Railway auto-detects build folder)
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | None |
| GET | `/webhook` | Meta webhook verification | None |
| POST | `/webhook` | Receive messages from Meta platforms | None |
| GET | `/api/admin/dashboard` | Dashboard statistics | API Key |
| GET | `/api/admin/leads` | List leads (paginated) | API Key |
| GET | `/api/admin/leads/{id}` | Get lead details | API Key |
| PATCH | `/api/admin/leads/{id}` | Update lead | API Key |
| GET | `/api/admin/leads/{id}/conversations` | Lead conversations | API Key |
| GET | `/api/admin/conversations/{id}/messages` | Conversation messages | API Key |
| GET | `/api/admin/properties` | Get properties data | API Key |

### Authentication

Admin API uses header-based authentication:

```bash
curl -H "X-API-Key: your_admin_api_key" https://your-domain.com/api/admin/dashboard
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Meta Platforms                        │
│         WhatsApp | Messenger | Instagram DM                 │
└────────────────────────┬────────────────────────────────────┘
                         │ Webhooks
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Webhook    │  │   Claude AI  │  │  Meta Graph  │     │
│  │   Handler    │─▶│   Service    │  │  API Service │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     Lead     │  │  Knowledge   │  │ Notification │     │
│  │   Service    │  │    Base      │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────┐          │
│  │         PostgreSQL Database                  │          │
│  │  Leads | Conversations | Messages | Projects │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                         ▲
                         │ REST API
                         │
┌─────────────────────────────────────────────────────────────┐
│              React Admin Dashboard                          │
│   Dashboard | Leads List | Conversations | Analytics        │
└─────────────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql://user:pass@localhost:5432/chatbot_db` |
| `ANTHROPIC_API_KEY` | Claude API key | Yes | `sk-ant-...` |
| `META_VERIFY_TOKEN` | Webhook verification token | Yes | `your_secure_token_123` |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp API access token | Yes | `EAAB...` |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | Yes | `123456789` |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | WABA ID | Yes | `123456789` |
| `MESSENGER_PAGE_ACCESS_TOKEN` | Messenger page token | Yes | `EAAB...` |
| `MESSENGER_PAGE_ID` | Facebook page ID | Yes | `123456789` |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram API token | Yes | `EAAB...` |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | IG business account ID | Yes | `123456789` |
| `ADMIN_API_KEY` | Admin dashboard API key | Yes | `admin_secret_key_xyz` |
| `SALES_TEAM_WHATSAPP` | Sales team WhatsApp for alerts | No | `201234567890` |
| `SALES_TEAM_EMAIL` | Sales team email | No | `sales@company.com` |
| `APP_ENV` | Environment (development/production) | No | `production` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## Testing

The project includes comprehensive test coverage using `pytest` with async support.

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_webhook.py -v
```

### Test Structure

- `tests/conftest.py` - Test fixtures and configuration
- `tests/test_webhook.py` - Webhook endpoint tests
- `tests/test_claude_service.py` - Claude AI service tests
- `tests/test_meta_service.py` - Meta API service tests
- `tests/test_lead_service.py` - Lead management tests
- `tests/test_admin.py` - Admin API tests

Tests use SQLite in-memory database for isolation and speed.

## Project Structure

```
real-estate-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + lifespan
│   ├── config.py               # Pydantic Settings
│   ├── database.py             # Async SQLAlchemy engine
│   ├── models/
│   │   ├── base.py             # Base model
│   │   ├── lead.py             # Lead model
│   │   ├── conversation.py     # Conversation + Message
│   │   └── property.py         # Project + Unit
│   ├── routers/
│   │   ├── webhook.py          # Webhook endpoints
│   │   ├── admin.py            # Admin API
│   │   └── health.py           # Health check
│   ├── services/
│   │   ├── claude_service.py   # Claude API
│   │   ├── meta_service.py     # Meta Graph API
│   │   ├── webhook_handler.py  # Message processing
│   │   ├── lead_service.py     # Lead CRUD
│   │   ├── knowledge.py        # Property data loader
│   │   └── notification_service.py
│   ├── schemas/
│   │   ├── webhook.py          # Webhook schemas
│   │   ├── admin.py            # Admin schemas
│   │   └── lead.py             # Lead schemas
│   └── prompts/
│       └── system_prompt.py    # System prompt builder
├── admin-panel/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── pages/
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
├── alembic/
│   └── versions/               # Database migrations
├── data/
│   └── properties.json         # Property knowledge base
├── tests/
│   ├── conftest.py
│   ├── test_webhook.py
│   ├── test_claude_service.py
│   ├── test_meta_service.py
│   ├── test_lead_service.py
│   └── test_admin.py
├── scripts/
│   └── seed_properties.py      # Database seeder
├── .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
├── Procfile                    # Railway deployment
└── README.md
```

## Development Notes

### Adding New Properties

1. Edit `data/properties.json` with new project data
2. Run seeder: `python scripts/seed_properties.py`
3. Properties are automatically included in AI context

### Database Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Prompt Caching

The Claude service uses prompt caching to reduce costs:
- System prompt (with property data) is cached as "ephemeral"
- Cache hits save ~90% of input token costs
- Cache TTL: 5 minutes of inactivity

### Rate Limits

- **Claude API**: 50 requests/minute (Haiku tier)
- **WhatsApp**: No rate limit for service messages (24h window)
- **Messenger**: 200 calls/hour
- **Instagram**: 200 calls/hour

All services implement automatic retry with exponential backoff.

## Business Logic

### Lead Classification

- **Hot**: Customer wants site visit, ready to book, asks about availability
- **Warm**: Asking detailed questions about prices, payment plans, specifications
- **Cold**: Just browsing, vague questions, minimal engagement

Classification happens automatically via Claude AI analysis.

### Language Detection

Bot responds in Arabic (Egyptian dialect) by default. Automatically switches to English if customer writes in English.

### 24-Hour Customer Service Window

- All platforms: Free messaging within 24 hours of last customer message
- WhatsApp: Template messages required outside 24h window (additional cost)
- Messenger & Instagram: Always free

## Troubleshooting

### Webhook Verification Failing

- Ensure `META_VERIFY_TOKEN` matches token in Meta App settings
- Check webhook URL is publicly accessible (use ngrok for local testing)

### Messages Not Being Received

- Verify webhook subscriptions in Meta App (messages field)
- Check Railway logs: `railway logs`
- Ensure phone number is in WhatsApp test number list

### Database Connection Issues

- Verify `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:port/db`
- Check PostgreSQL is running and accessible
- On Railway, ensure database service is linked

### Claude API Errors

- Verify `ANTHROPIC_API_KEY` is valid
- Check API quota/rate limits
- Review logs for specific error messages

## License

Proprietary - All rights reserved

---

**Need Help?** Check Meta's [WhatsApp Business Platform documentation](https://developers.facebook.com/docs/whatsapp) and [Anthropic's Claude API docs](https://docs.anthropic.com/).
