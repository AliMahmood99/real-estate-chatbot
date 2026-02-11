"""Seed the database with property data from properties.json."""

import asyncio
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session, engine
from app.models.base import Base
from app.models.property import Project, Unit


async def seed_properties():
    """Load properties from JSON and insert into database."""
    # Load JSON data
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "properties.json")

    if not os.path.exists(data_path):
        print(f"Error: properties.json not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nLoading properties for: {data.get('company_name', 'Unknown Company')}")
    print("-" * 60)

    async with async_session() as session:
        for project_data in data.get("projects", []):
            # Create project
            project = Project(
                name=project_data["name"],
                developer=project_data["developer"],
                location=project_data["location"],
                area=project_data["area"],
                description=project_data.get("description"),
                amenities=project_data.get("amenities", []),
                delivery_status=project_data.get("delivery_status"),
            )
            session.add(project)
            await session.flush()  # Get project.id

            # Create units
            unit_count = 0
            for unit_data in project_data.get("units", []):
                unit = Unit(
                    project_id=project.id,
                    type=unit_data["type"],
                    size_from=unit_data.get("size_from"),
                    size_to=unit_data.get("size_to"),
                    price_from=unit_data.get("price_from"),
                    price_to=unit_data.get("price_to"),
                    floor_options=unit_data.get("floors"),
                    views=unit_data.get("views", []),
                    payment_plans=project_data.get("payment_plans", []),
                    availability_status="available",
                )
                session.add(unit)
                unit_count += 1

            print(f"  ✓ Seeded project: {project_data['name']}")
            print(f"    - Location: {project_data['location']}")
            print(f"    - Unit types: {unit_count}")
            print(f"    - Delivery: {project_data.get('delivery_status', 'N/A')}")
            print()

        await session.commit()
        print("=" * 60)
        print("All properties seeded successfully!")
        print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("REAL ESTATE CHATBOT - PROPERTY SEEDER")
    print("=" * 60)

    try:
        asyncio.run(seed_properties())
    except Exception as e:
        print(f"\n❌ Error seeding properties: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
