"""Test fixtures and configuration."""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models.base import Base
from app.models import Lead, Conversation, Message, Project, Unit
from app.models.lead import Platform, LeadStatus
from app.models.conversation import SenderType
from app.database import get_db
from app.main import app
from app.config import get_settings


# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Override database dependency for testing."""
    async with test_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    """Provide a test database session."""
    async with test_async_session() as session:
        yield session


@pytest_asyncio.fixture
async def sample_lead(db_session):
    """Create a sample lead for testing."""
    lead = Lead(
        platform_sender_id="201234567890",
        platform=Platform.WHATSAPP,
        name="أحمد محمد",
        phone="201234567890",
        status=LeadStatus.NEW,
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead


@pytest_asyncio.fixture
async def sample_conversation(db_session, sample_lead):
    """Create a sample conversation."""
    conv = Conversation(
        lead_id=sample_lead.id,
        platform="whatsapp",
        message_count=2,
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # Add messages
    msg1 = Message(
        conversation_id=conv.id,
        sender_type=SenderType.CUSTOMER,
        content="عايز أعرف أسعار الشقق",
        platform="whatsapp",
    )
    msg2 = Message(
        conversation_id=conv.id,
        sender_type=SenderType.BOT,
        content="أهلاً بيك! عندنا مشاريع كتير...",
        platform="whatsapp",
    )
    db_session.add_all([msg1, msg2])
    await db_session.commit()
    return conv


# Sample webhook payloads
WHATSAPP_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WABA_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"phone_number_id": "PHONE_ID"},
                "messages": [{
                    "from": "201234567890",
                    "id": "wamid.xxx",
                    "timestamp": "1234567890",
                    "type": "text",
                    "text": {"body": "عايز أعرف أسعار الشقق"}
                }]
            },
            "field": "messages"
        }]
    }]
}

MESSENGER_PAYLOAD = {
    "object": "page",
    "entry": [{
        "id": "PAGE_ID",
        "time": 1234567890,
        "messaging": [{
            "sender": {"id": "USER_123"},
            "recipient": {"id": "PAGE_ID"},
            "timestamp": 1234567890,
            "message": {
                "mid": "m_xxx",
                "text": "عايز أعرف أسعار الشقق"
            }
        }]
    }]
}

INSTAGRAM_PAYLOAD = {
    "object": "instagram",
    "entry": [{
        "id": "IG_ID",
        "time": 1234567890,
        "messaging": [{
            "sender": {"id": "IG_USER_123"},
            "recipient": {"id": "IG_ID"},
            "timestamp": 1234567890,
            "message": {
                "mid": "m_xxx",
                "text": "عايز أعرف أسعار الشقق"
            }
        }]
    }]
}

WHATSAPP_STATUS_UPDATE = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WABA_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"phone_number_id": "PHONE_ID"},
                "statuses": [{
                    "id": "wamid.xxx",
                    "status": "delivered",
                    "timestamp": "1234567890"
                }]
            },
            "field": "messages"
        }]
    }]
}
