"""Tests for admin API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead, LeadStatus, Platform
from app.config import get_settings

settings = get_settings()


class TestAdminAuth:
    """Test admin API authentication."""

    @pytest.mark.asyncio
    async def test_unauthorized_access_rejected(self, client: AsyncClient):
        """Test that requests without API key are rejected."""
        response = await client.get("/api/admin/dashboard")

        # Should return 422 (missing required header) or 401
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_invalid_api_key_rejected(self, client: AsyncClient):
        """Test that requests with invalid API key are rejected."""
        response = await client.get(
            "/api/admin/dashboard",
            headers={"X-API-Key": "invalid_key_12345"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_api_key_accepted(self, client: AsyncClient, sample_lead: Lead):
        """Test that requests with valid API key are accepted."""
        # Use actual API key from settings, or skip if not set
        if not settings.ADMIN_API_KEY:
            pytest.skip("ADMIN_API_KEY not set in test environment")

        response = await client.get(
            "/api/admin/dashboard",
            headers={"X-API-Key": settings.ADMIN_API_KEY}
        )

        assert response.status_code == 200


class TestDashboardStats:
    """Test dashboard statistics endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting dashboard statistics."""
        # Create some test leads
        leads = [
            Lead(
                platform_sender_id=f"2011111111{i}",
                platform=Platform.WHATSAPP,
                name=f"Lead {i}",
                status=LeadStatus.NEW if i % 2 == 0 else LeadStatus.HOT,
            )
            for i in range(5)
        ]
        db_session.add_all(leads)
        await db_session.commit()

        # Mock API key for testing
        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                "/api/admin/dashboard",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "leads_today" in data
                assert "leads_this_week" in data
                assert "leads_this_month" in data
                assert "leads_by_platform" in data
                assert "leads_by_status" in data
                assert "top_projects" in data
                assert "recent_leads" in data

                # Verify counts
                assert data["leads_today"] >= 0
                assert isinstance(data["leads_by_platform"], dict)
                assert isinstance(data["leads_by_status"], dict)


class TestLeadsList:
    """Test leads list endpoint."""

    @pytest.mark.asyncio
    async def test_leads_list(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting paginated leads list."""
        # Create test leads
        leads = [
            Lead(
                platform_sender_id=f"2022222222{i}",
                platform=Platform.WHATSAPP,
                name=f"Test Lead {i}",
                status=LeadStatus.NEW,
            )
            for i in range(3)
        ]
        db_session.add_all(leads)
        await db_session.commit()

        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                "/api/admin/leads",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                # Verify pagination structure
                assert "items" in data
                assert "page" in data
                assert "per_page" in data
                assert "total" in data
                assert "pages" in data

                assert isinstance(data["items"], list)
                assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_leads_list_with_filters(self, client: AsyncClient, db_session: AsyncSession):
        """Test leads list with platform filter."""
        # Create leads on different platforms
        leads = [
            Lead(
                platform_sender_id="201111111111",
                platform=Platform.WHATSAPP,
                status=LeadStatus.NEW,
            ),
            Lead(
                platform_sender_id="202222222222",
                platform=Platform.MESSENGER,
                status=LeadStatus.HOT,
            ),
        ]
        db_session.add_all(leads)
        await db_session.commit()

        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                "/api/admin/leads?platform=whatsapp",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                # All returned leads should be WhatsApp
                for item in data["items"]:
                    assert item["platform"] == "whatsapp"


class TestLeadDetail:
    """Test single lead detail endpoint."""

    @pytest.mark.asyncio
    async def test_lead_detail(self, client: AsyncClient, sample_lead: Lead):
        """Test getting single lead detail."""
        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                f"/api/admin/leads/{sample_lead.id}",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                # Verify lead data
                assert data["id"] == str(sample_lead.id)
                assert data["platform_sender_id"] == sample_lead.platform_sender_id
                assert data["platform"] == sample_lead.platform.value
                assert data["name"] == sample_lead.name

    @pytest.mark.asyncio
    async def test_lead_detail_not_found(self, client: AsyncClient):
        """Test getting non-existent lead returns 404."""
        from uuid import uuid4

        fake_id = uuid4()
        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                f"/api/admin/leads/{fake_id}",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 404


class TestLeadUpdate:
    """Test lead update endpoint."""

    @pytest.mark.asyncio
    async def test_lead_update(self, client: AsyncClient, sample_lead: Lead):
        """Test updating lead fields."""
        api_key = settings.ADMIN_API_KEY or "test_api_key"
        update_data = {
            "status": "hot",
            "notes": "Very interested in Nasr City properties"
        }

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.patch(
                f"/api/admin/leads/{sample_lead.id}",
                headers={"X-API-Key": api_key},
                json=update_data
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                # Verify updated fields
                assert data["status"] == "hot"
                assert data["notes"] == "Very interested in Nasr City properties"

    @pytest.mark.asyncio
    async def test_lead_update_invalid_status(self, client: AsyncClient, sample_lead: Lead):
        """Test updating lead with invalid status."""
        api_key = settings.ADMIN_API_KEY or "test_api_key"
        update_data = {
            "status": "invalid_status_value"
        }

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.patch(
                f"/api/admin/leads/{sample_lead.id}",
                headers={"X-API-Key": api_key},
                json=update_data
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 400


class TestConversations:
    """Test conversation endpoints."""

    @pytest.mark.asyncio
    async def test_get_lead_conversations(self, client: AsyncClient, sample_conversation):
        """Test getting conversations for a lead."""
        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                f"/api/admin/leads/{sample_conversation.lead_id}/conversations",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                assert isinstance(data, list)
                assert len(data) >= 1

                # Verify conversation structure
                conv = data[0]
                assert "id" in conv
                assert "lead_id" in conv
                assert "platform" in conv
                assert "message_count" in conv

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, client: AsyncClient, sample_conversation):
        """Test getting messages in a conversation."""
        api_key = settings.ADMIN_API_KEY or "test_api_key"

        with pytest.MonkeyPatch.context() as m:
            if not settings.ADMIN_API_KEY:
                m.setattr("app.config.Settings.ADMIN_API_KEY", "test_api_key")

            response = await client.get(
                f"/api/admin/conversations/{sample_conversation.id}/messages",
                headers={"X-API-Key": api_key}
            )

            if settings.ADMIN_API_KEY:
                assert response.status_code == 200
                data = response.json()

                assert isinstance(data, list)
                assert len(data) == 2  # From fixture

                # Verify message structure
                msg = data[0]
                assert "id" in msg
                assert "conversation_id" in msg
                assert "sender_type" in msg
                assert "content" in msg
                assert "timestamp" in msg
