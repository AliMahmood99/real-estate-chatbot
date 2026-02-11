"""Tests for Claude AI service."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.claude_service import generate_response, _parse_response
import anthropic


class TestClaudeService:
    """Test Claude AI service functionality."""

    @pytest.mark.asyncio
    async def test_generate_response_returns_reply(self):
        """Test that generate_response returns a dict with reply key."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="أهلاً بيك! عندنا مشاريع كتير في الشيخ زايد.")]

        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.messages.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            conversation_history = [
                {"role": "user", "content": "عايز أعرف أسعار الشقق"}
            ]
            property_data = "Sample property data"

            result = await generate_response(conversation_history, property_data)

            assert isinstance(result, dict)
            assert "reply" in result
            assert "lead_data" in result
            assert isinstance(result["reply"], str)
            assert len(result["reply"]) > 0
            assert result["lead_data"] == {}

    @pytest.mark.asyncio
    async def test_extract_lead_data_from_response(self):
        """Test that lead data is correctly extracted from response with JSON block."""
        mock_response_text = """أهلاً بيك! عندنا مشاريع كتير في الشيخ زايد.

---LEAD_DATA---
{"name": "أحمد محمد", "phone": "01234567890", "classification": "warm"}
---END_LEAD_DATA---"""

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=mock_response_text)]

        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.messages.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            conversation_history = [
                {"role": "user", "content": "اسمي أحمد ورقمي 01234567890"}
            ]
            property_data = "Sample property data"

            result = await generate_response(conversation_history, property_data)

            assert "reply" in result
            assert "lead_data" in result
            # Reply should NOT contain the JSON block
            assert "---LEAD_DATA---" not in result["reply"]
            assert "---END_LEAD_DATA---" not in result["reply"]
            # Lead data should be extracted
            assert result["lead_data"]["name"] == "أحمد محمد"
            assert result["lead_data"]["phone"] == "01234567890"
            assert result["lead_data"]["classification"] == "warm"

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        """Test that API errors are handled gracefully with fallback message."""
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.messages.create = AsyncMock(
                side_effect=anthropic.APIError("API Error")
            )
            mock_client.return_value = mock_instance

            conversation_history = [
                {"role": "user", "content": "عايز أعرف أسعار الشقق"}
            ]
            property_data = "Sample property data"

            result = await generate_response(conversation_history, property_data)

            # Should return fallback message
            assert isinstance(result, dict)
            assert "reply" in result
            assert "عذراً" in result["reply"] or "مشكلة" in result["reply"]
            assert result["lead_data"] == {}

    @pytest.mark.asyncio
    async def test_handles_timeout_error(self):
        """Test handling of API timeout errors."""
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.messages.create = AsyncMock(
                side_effect=anthropic.APITimeoutError("Timeout")
            )
            mock_client.return_value = mock_instance

            conversation_history = [
                {"role": "user", "content": "عايز أعرف أسعار الشقق"}
            ]
            property_data = "Sample property data"

            result = await generate_response(conversation_history, property_data)

            # Should return timeout-specific message
            assert isinstance(result, dict)
            assert "reply" in result
            assert result["lead_data"] == {}

    @pytest.mark.asyncio
    async def test_handles_rate_limit_error(self):
        """Test handling of API rate limit errors."""
        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.messages.create = AsyncMock(
                side_effect=anthropic.RateLimitError("Rate limit exceeded")
            )
            mock_client.return_value = mock_instance

            conversation_history = [
                {"role": "user", "content": "عايز أعرف أسعار الشقق"}
            ]
            property_data = "Sample property data"

            result = await generate_response(conversation_history, property_data)

            # Should return rate limit message
            assert isinstance(result, dict)
            assert "reply" in result
            assert result["lead_data"] == {}

    @pytest.mark.asyncio
    async def test_response_without_lead_data(self):
        """Test response without lead data block returns empty dict for lead_data."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="أهلاً بيك! عندنا مشاريع كتير.")]

        with patch('anthropic.AsyncAnthropic') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.messages.create = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_instance

            conversation_history = [
                {"role": "user", "content": "عايز أعرف أسعار الشقق"}
            ]
            property_data = "Sample property data"

            result = await generate_response(conversation_history, property_data)

            assert result["lead_data"] == {}
            assert len(result["reply"]) > 0


class TestParseResponse:
    """Test the _parse_response helper function."""

    def test_parse_response_with_lead_data(self):
        """Test parsing response with lead data block."""
        response_text = """مرحباً بيك!

---LEAD_DATA---
{"name": "أحمد", "classification": "hot"}
---END_LEAD_DATA---"""

        clean_reply, lead_data = _parse_response(response_text)

        assert "---LEAD_DATA---" not in clean_reply
        assert "مرحباً بيك!" in clean_reply
        assert lead_data["name"] == "أحمد"
        assert lead_data["classification"] == "hot"

    def test_parse_response_without_lead_data(self):
        """Test parsing response without lead data block."""
        response_text = "مرحباً بيك! عندنا مشاريع كتير."

        clean_reply, lead_data = _parse_response(response_text)

        assert clean_reply == "مرحباً بيك! عندنا مشاريع كتير."
        assert lead_data == {}

    def test_parse_response_with_invalid_json(self):
        """Test parsing response with invalid JSON in lead data block."""
        response_text = """مرحباً بيك!

---LEAD_DATA---
{invalid json here}
---END_LEAD_DATA---"""

        clean_reply, lead_data = _parse_response(response_text)

        # Should still extract clean reply but return empty dict for lead_data
        assert "مرحباً بيك!" in clean_reply
        assert lead_data == {}

    def test_parse_response_filters_null_values(self):
        """Test that null values are filtered from lead data."""
        response_text = """مرحباً!

---LEAD_DATA---
{"name": "أحمد", "phone": null, "email": null}
---END_LEAD_DATA---"""

        clean_reply, lead_data = _parse_response(response_text)

        # Null values should be filtered out
        assert "name" in lead_data
        assert "phone" not in lead_data
        assert "email" not in lead_data
