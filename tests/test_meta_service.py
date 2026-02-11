"""Tests for Meta API service."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from app.services.meta_service import send_text_message, _send_whatsapp_message, _send_messenger_message, _send_instagram_message
from app.config import get_settings

settings = get_settings()


class TestMetaService:
    """Test Meta API service for sending messages."""

    @pytest.mark.asyncio
    async def test_send_whatsapp_message(self):
        """Test sending WhatsApp message with correct URL and body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.xxx"}]}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            success = await send_text_message("whatsapp", "201234567890", "مرحباً!")

            assert success is True
            mock_instance.post.assert_called_once()

            # Verify correct URL was used
            call_args = mock_instance.post.call_args
            assert "graph.facebook.com" in call_args[0][0]
            assert "messages" in call_args[0][0]

            # Verify payload structure
            payload = call_args[1]["json"]
            assert payload["messaging_product"] == "whatsapp"
            assert payload["to"] == "201234567890"
            assert payload["type"] == "text"
            assert payload["text"]["body"] == "مرحباً!"

    @pytest.mark.asyncio
    async def test_send_messenger_message(self):
        """Test sending Messenger message with correct URL and body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message_id": "mid.xxx"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            success = await send_text_message("messenger", "USER_123", "Hello!")

            assert success is True
            # Should be called twice: typing indicator + message
            assert mock_instance.post.call_count == 2

            # Check the message call (second call)
            message_call = mock_instance.post.call_args_list[1]
            assert "graph.facebook.com" in message_call[0][0]
            assert "me/messages" in message_call[0][0]

            # Verify payload structure
            payload = message_call[1]["json"]
            assert payload["recipient"]["id"] == "USER_123"
            assert payload["message"]["text"] == "Hello!"

    @pytest.mark.asyncio
    async def test_send_instagram_message(self):
        """Test sending Instagram message with correct URL and body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message_id": "mid.xxx"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            success = await send_text_message("instagram", "IG_USER_123", "Hi there!")

            assert success is True
            # Should be called twice: typing indicator + message
            assert mock_instance.post.call_count == 2

            # Check the message call (second call)
            message_call = mock_instance.post.call_args_list[1]
            assert "graph.facebook.com" in message_call[0][0]
            assert "me/messages" in message_call[0][0]

            # Verify payload structure
            payload = message_call[1]["json"]
            assert payload["recipient"]["id"] == "IG_USER_123"
            assert payload["message"]["text"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that the service retries on failure then succeeds."""
        # First call fails, second succeeds
        mock_fail_response = MagicMock()
        mock_fail_response.status_code = 500
        mock_fail_response.text = "Internal Server Error"

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"messages": [{"id": "wamid.xxx"}]}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()

            # First call raises HTTPStatusError, second succeeds
            async def side_effect(*args, **kwargs):
                if mock_instance.post.call_count == 1:
                    error = httpx.HTTPStatusError(
                        "Server Error",
                        request=MagicMock(),
                        response=mock_fail_response
                    )
                    raise error
                return mock_success_response

            mock_instance.post = AsyncMock(side_effect=side_effect)
            mock_client.return_value = mock_instance

            success = await send_text_message("whatsapp", "201234567890", "Test retry")

            # Should eventually succeed after retry
            assert success is True
            assert mock_instance.post.call_count == 2

    @pytest.mark.asyncio
    async def test_rate_limit_retry(self):
        """Test retry behavior on rate limit (429) errors."""
        mock_rate_limit_response = MagicMock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.text = "Rate limit exceeded"

        mock_success_response = MagicMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"messages": [{"id": "wamid.xxx"}]}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()

            # First call returns 429, second succeeds
            async def side_effect(*args, **kwargs):
                if mock_instance.post.call_count == 1:
                    error = httpx.HTTPStatusError(
                        "Rate Limit",
                        request=MagicMock(),
                        response=mock_rate_limit_response
                    )
                    raise error
                return mock_success_response

            mock_instance.post = AsyncMock(side_effect=side_effect)
            mock_client.return_value = mock_instance

            success = await send_text_message("whatsapp", "201234567890", "Test")

            # Should retry and succeed
            assert success is True
            assert mock_instance.post.call_count == 2

    @pytest.mark.asyncio
    async def test_unknown_platform_returns_false(self):
        """Test that unknown platform returns False."""
        success = await send_text_message("unknown_platform", "12345", "Test")

        assert success is False

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that function returns False after max retries."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()

            # Always fail
            async def side_effect(*args, **kwargs):
                error = httpx.HTTPStatusError(
                    "Server Error",
                    request=MagicMock(),
                    response=mock_response
                )
                raise error

            mock_instance.post = AsyncMock(side_effect=side_effect)
            mock_client.return_value = mock_instance

            success = await send_text_message("whatsapp", "201234567890", "Test")

            # Should fail after 3 attempts
            assert success is False
            assert mock_instance.post.call_count == 3
