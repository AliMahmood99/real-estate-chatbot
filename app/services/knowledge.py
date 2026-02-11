"""Property data knowledge base loader."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache for property data
_property_data_cache: str | None = None


async def load_properties() -> str:
    """
    Load property data from JSON file and format as readable text.
    Data is cached in memory after first load.

    Returns:
        Formatted property data string for use in system prompt
    """
    global _property_data_cache

    # Return cached data if available
    if _property_data_cache is not None:
        return _property_data_cache

    try:
        # Locate properties.json file
        project_root = Path(__file__).parent.parent.parent
        properties_file = project_root / "data" / "properties.json"

        if not properties_file.exists():
            logger.error(f"Properties file not found at {properties_file}")
            return _get_fallback_data()

        # Load JSON data
        with open(properties_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Format data as readable text
        formatted_data = _format_properties(data)

        # Cache the result
        _property_data_cache = formatted_data

        logger.info(f"Property data loaded successfully: {len(formatted_data)} chars")
        return formatted_data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in properties file: {e}")
        return _get_fallback_data()

    except Exception as e:
        logger.error(f"Error loading properties: {e}", exc_info=True)
        return _get_fallback_data()


def _format_properties(data: dict[str, Any]) -> str:
    """
    Format property data as readable text for the system prompt.

    Args:
        data: Property data dictionary from JSON

    Returns:
        Formatted string with all property information
    """
    if not data or "projects" not in data:
        return "لا توجد مشاريع متاحة حالياً."

    projects = data["projects"]
    formatted_text = []

    for project in projects:
        project_name = project.get("name", "مشروع غير معروف")
        developer = project.get("developer", "")
        location = project.get("location", "")
        area = project.get("area", "")
        description = project.get("description", "")
        amenities = project.get("amenities", [])
        delivery_status = project.get("delivery_status", "")
        units = project.get("units", [])

        # Build project section
        project_text = [f"\n### {project_name}"]

        if developer:
            project_text.append(f"المطور: {developer}")

        if location:
            project_text.append(f"الموقع: {location}")

        if area:
            project_text.append(f"المنطقة: {area}")

        if description:
            project_text.append(f"الوصف: {description}")

        if delivery_status:
            project_text.append(f"حالة التسليم: {delivery_status}")

        if amenities:
            amenities_text = "، ".join(amenities)
            project_text.append(f"المرافق: {amenities_text}")

        # Add units
        if units:
            project_text.append("\nالوحدات المتاحة:")
            for unit in units:
                unit_text = _format_unit(unit)
                project_text.append(unit_text)

        formatted_text.append("\n".join(project_text))

    return "\n\n".join(formatted_text)


def _format_unit(unit: dict[str, Any]) -> str:
    """
    Format a single unit as readable text.

    Args:
        unit: Unit data dictionary

    Returns:
        Formatted unit description
    """
    unit_type = unit.get("type", "وحدة")
    lines = [f"- {unit_type}"]

    # Size range
    size_from = unit.get("size_from")
    size_to = unit.get("size_to")
    if size_from and size_to:
        lines.append(f"  المساحة: من {size_from} إلى {size_to} متر مربع")
    elif size_from:
        lines.append(f"  المساحة: {size_from} متر مربع")

    # Price range
    price_from = unit.get("price_from")
    price_to = unit.get("price_to")
    if price_from and price_to:
        lines.append(f"  السعر: من {price_from:,.0f} إلى {price_to:,.0f} جنيه")
    elif price_from:
        lines.append(f"  السعر: {price_from:,.0f} جنيه")

    # Floor options
    floor_options = unit.get("floor_options")
    if floor_options:
        lines.append(f"  الأدوار: {floor_options}")

    # Views
    views = unit.get("views", [])
    if views:
        views_text = "، ".join(views)
        lines.append(f"  الإطلالات: {views_text}")

    # Payment plans
    payment_plans = unit.get("payment_plans", [])
    if payment_plans:
        lines.append("  أنظمة السداد:")
        for plan in payment_plans:
            if isinstance(plan, str):
                lines.append(f"    • {plan}")
            elif isinstance(plan, dict):
                plan_desc = plan.get("description", "")
                if plan_desc:
                    lines.append(f"    • {plan_desc}")

    # Availability
    availability = unit.get("availability_status", "")
    if availability and availability != "available":
        lines.append(f"  التوافر: {availability}")

    return "\n".join(lines)


def _get_fallback_data() -> str:
    """Return fallback message when property data cannot be loaded."""
    return """عذراً، حصل مشكلة في تحميل بيانات المشاريع.
الرجاء التواصل مع فريق المبيعات مباشرة للحصول على المعلومات الكاملة."""
