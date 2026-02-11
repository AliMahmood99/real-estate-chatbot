"""Claude API service for generating AI responses."""

import logging
import json
import re
from typing import Any
import anthropic
from app.config import get_settings
from app.prompts.system_prompt import build_system_prompt

logger = logging.getLogger(__name__)
settings = get_settings()

# Claude API configuration
MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024


async def generate_response(
    conversation_history: list[dict[str, str]],
    property_data: str
) -> dict[str, Any]:
    """
    Generate AI response using Claude API with prompt caching.

    Args:
        conversation_history: List of conversation messages with role and content
        property_data: Formatted property data string for context

    Returns:
        Dictionary with "reply" (clean text) and "lead_data" (extracted JSON dict)
    """
    try:
        # Build system prompt with caching
        system_prompt = build_system_prompt(property_data)

        # Initialize Claude client
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Call Claude API with prompt caching
        message = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=conversation_history
        )

        # Extract response text
        response_text = message.content[0].text

        # Parse response: extract clean reply and lead data
        clean_reply, lead_data = _parse_response(response_text)

        logger.info(f"Claude response generated: {len(clean_reply)} chars, lead_data: {bool(lead_data)}")
        logger.debug(f"Lead data extracted: {lead_data}")

        return {
            "reply": clean_reply,
            "lead_data": lead_data
        }

    except anthropic.APITimeoutError as e:
        logger.error(f"Claude API timeout: {e}")
        return {
            "reply": "عذراً، الرد استغرق وقت طويل. ممكن تعيد المحاولة؟",
            "lead_data": {}
        }

    except anthropic.RateLimitError as e:
        logger.error(f"Claude API rate limit: {e}")
        return {
            "reply": "عذراً، النظام مشغول دلوقتي. جرب تاني بعد شوية.",
            "lead_data": {}
        }

    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return {
            "reply": "عذراً، حصل مشكلة تقنية. حاول تاني بعد شوية.",
            "lead_data": {}
        }

    except Exception as e:
        logger.error(f"Unexpected error generating Claude response: {e}", exc_info=True)
        return {
            "reply": "عذراً، حصل خطأ غير متوقع. ممكن تجرب تاني؟",
            "lead_data": {}
        }


def _parse_response(response_text: str) -> tuple[str, dict[str, Any]]:
    """
    Parse Claude response to extract clean reply text and lead data JSON.

    The expected format is:
    [Clean response text]
    ---LEAD_DATA---
    {"name": "...", "phone": "...", ...}
    ---END_LEAD_DATA---

    Args:
        response_text: Raw response text from Claude

    Returns:
        Tuple of (clean_reply_text, lead_data_dict)
    """
    # Pattern to match the lead data block
    pattern = r'---LEAD_DATA---\s*(\{.*?\})\s*---END_LEAD_DATA---'

    match = re.search(pattern, response_text, re.DOTALL)

    if match:
        # Extract JSON block
        json_str = match.group(1).strip()

        # Remove the entire lead data block from the response
        clean_reply = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()

        try:
            # Parse JSON
            lead_data = json.loads(json_str)

            # Filter out null values
            lead_data = {k: v for k, v in lead_data.items() if v is not None}

            return clean_reply, lead_data

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse lead data JSON: {e}")
            logger.debug(f"Invalid JSON: {json_str}")
            return clean_reply, {}

    # No lead data block found
    return response_text.strip(), {}
