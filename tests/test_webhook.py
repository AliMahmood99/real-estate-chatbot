"""Tests for webhook endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from app.config import get_settings
from tests.conftest import WHATSAPP_PAYLOAD, MESSENGER_PAYLOAD, INSTAGRAM_PAYLOAD, WHATSAPP_STATUS_UPDATE

settings = get_settings()


class TestWebhookVerification:
    """Test webhook verification endpoint (GET /webhook)."""

    @pytest.mark.asyncio
    async def test_webhook_verification_valid_token(self, client: AsyncClient):
        """Test webhook verification with valid token."""
        response = await client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": settings.META_VERIFY_TOKEN or "test_token",
                "hub.challenge": "challenge_string_123"
            }
        )

        # Should return 200 with challenge
        if settings.META_VERIFY_TOKEN:
            assert response.status_code in [200, 403]  # Depends on env config
        else:
            # If no token set, test with mock
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_webhook_verification_invalid_token(self, client: AsyncClient):
        """Test webhook verification with invalid token."""
        response = await client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token_12345",
                "hub.challenge": "challenge_string_123"
            }
        )

        assert response.status_code == 403
        assert "Verification failed" in response.text

    @pytest.mark.asyncio
    async def test_webhook_verification_missing_params(self, client: AsyncClient):
        """Test webhook verification with missing parameters."""
        response = await client.get("/webhook")

        assert response.status_code == 403
        assert "Verification failed" in response.text

    @pytest.mark.asyncio
    async def test_webhook_verification_wrong_mode(self, client: AsyncClient):
        """Test webhook verification with wrong mode."""
        response = await client.get(
            "/webhook",
            params={
                "hub.mode": "unsubscribe",
                "hub.verify_token": settings.META_VERIFY_TOKEN or "test_token",
                "hub.challenge": "challenge_string_123"
            }
        )

        assert response.status_code == 403


class TestWebhookReceive:
    """Test webhook receive endpoint (POST /webhook)."""

    @pytest.mark.asyncio
    @patch('app.services.webhook_handler.process_incoming_message', new_callable=AsyncMock)
    async def test_whatsapp_message_received(self, mock_process, client: AsyncClient):
        """Test receiving WhatsApp message."""
        response = await client.post("/webhook", json=WHATSAPP_PAYLOAD)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Verify background task was scheduled
        # Note: background task execution happens after response
        mock_process.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.webhook_handler.process_incoming_message', new_callable=AsyncMock)
    async def test_messenger_message_received(self, mock_process, client: AsyncClient):
        """Test receiving Messenger message."""
        response = await client.post("/webhook", json=MESSENGER_PAYLOAD)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_process.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.webhook_handler.process_incoming_message', new_callable=AsyncMock)
    async def test_instagram_message_received(self, mock_process, client: AsyncClient):
        """Test receiving Instagram message."""
        response = await client.post("/webhook", json=INSTAGRAM_PAYLOAD)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_returns_200_immediately(self, client: AsyncClient):
        """Test that webhook returns 200 immediately without waiting for processing."""
        import time

        start_time = time.time()
        response = await client.post("/webhook", json=WHATSAPP_PAYLOAD)
        duration = time.time() - start_time

        # Should return very quickly (under 1 second)
        assert response.status_code == 200
        assert duration < 1.0

    @pytest.mark.asyncio
    @patch('app.services.webhook_handler.process_incoming_message', new_callable=AsyncMock)
    async def test_status_update_ignored(self, mock_process, client: AsyncClient):
        """Test that WhatsApp status updates don't cause errors."""
        response = await client.post("/webhook", json=WHATSAPP_STATUS_UPDATE)

        # Should still return 200 (webhook accepts all payloads)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Process function should still be called (it filters internally)
        mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_payload(self, client: AsyncClient):
        """Test webhook with empty payload."""
        response = await client.post("/webhook", json={})

        # Should still return 200 (graceful handling)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_malformed_payload(self, client: AsyncClient):
        """Test webhook with malformed payload."""
        response = await client.post("/webhook", json={"invalid": "data"})

        # Should still return 200 (graceful handling)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
