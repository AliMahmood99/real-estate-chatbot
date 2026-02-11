"""Tests for lead service."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead, LeadStatus, Platform
from app.services.lead_service import (
    get_or_create_lead,
    update_lead_from_ai,
    classify_lead,
    get_lead_by_id,
)


class TestLeadService:
    """Test lead service functionality."""

    @pytest.mark.asyncio
    async def test_create_new_lead(self, db_session: AsyncSession):
        """Test creating a new lead."""
        lead = await get_or_create_lead(db_session, "whatsapp", "201111111111")

        assert lead is not None
        assert lead.id is not None
        assert lead.platform == Platform.WHATSAPP
        assert lead.platform_sender_id == "201111111111"
        assert lead.status == LeadStatus.NEW

        # Verify it was saved to database
        result = await db_session.execute(
            select(Lead).where(Lead.platform_sender_id == "201111111111")
        )
        db_lead = result.scalar_one_or_none()
        assert db_lead is not None
        assert db_lead.id == lead.id

    @pytest.mark.asyncio
    async def test_get_existing_lead(self, db_session: AsyncSession):
        """Test getting an existing lead with same sender_id."""
        # Create first lead
        lead1 = await get_or_create_lead(db_session, "whatsapp", "201222222222")
        await db_session.commit()
        lead1_id = lead1.id

        # Get same lead again
        lead2 = await get_or_create_lead(db_session, "whatsapp", "201222222222")

        # Should be the same lead
        assert lead2.id == lead1_id
        assert lead2.platform_sender_id == "201222222222"

        # Verify only one lead exists in database
        result = await db_session.execute(
            select(Lead).where(Lead.platform_sender_id == "201222222222")
        )
        leads = result.scalars().all()
        assert len(leads) == 1

    @pytest.mark.asyncio
    async def test_update_lead_from_ai_data(self, db_session: AsyncSession, sample_lead: Lead):
        """Test updating lead with AI-extracted data."""
        ai_data = {
            "name": "محمد علي",
            "phone": "201555555555",
            "budget": "3-5 مليون جنيه",
            "timeline": "3 شهور",
            "interested_project": "نخيل ريزيدنس",
        }

        updated_lead = await update_lead_from_ai(db_session, sample_lead.id, ai_data)
        await db_session.commit()

        assert updated_lead is not None
        assert updated_lead.name == "محمد علي"
        assert updated_lead.phone == "201555555555"
        assert updated_lead.budget_range == "3-5 مليون جنيه"
        assert updated_lead.timeline == "3 شهور"
        assert "نخيل ريزيدنس" in updated_lead.interested_projects

    @pytest.mark.asyncio
    async def test_update_lead_classification(self, db_session: AsyncSession, sample_lead: Lead):
        """Test updating lead with classification."""
        ai_data = {
            "classification": "hot"
        }

        updated_lead = await update_lead_from_ai(db_session, sample_lead.id, ai_data)
        await db_session.commit()

        assert updated_lead is not None
        assert updated_lead.status == LeadStatus.HOT

    @pytest.mark.asyncio
    async def test_update_lead_adds_to_interested_projects(self, db_session: AsyncSession, sample_lead: Lead):
        """Test that interested projects are added, not replaced."""
        # Add first project
        ai_data_1 = {"interested_project": "نخيل ريزيدنس"}
        await update_lead_from_ai(db_session, sample_lead.id, ai_data_1)
        await db_session.commit()

        # Add second project
        ai_data_2 = {"interested_project": "النخيل كابيتال"}
        updated_lead = await update_lead_from_ai(db_session, sample_lead.id, ai_data_2)
        await db_session.commit()

        # Both projects should be in the list
        assert len(updated_lead.interested_projects) == 2
        assert "نخيل ريزيدنس" in updated_lead.interested_projects
        assert "النخيل كابيتال" in updated_lead.interested_projects

    @pytest.mark.asyncio
    async def test_update_lead_with_empty_data(self, db_session: AsyncSession, sample_lead: Lead):
        """Test updating lead with empty data doesn't change anything."""
        original_name = sample_lead.name
        original_status = sample_lead.status

        ai_data = {}
        updated_lead = await update_lead_from_ai(db_session, sample_lead.id, ai_data)

        assert updated_lead.name == original_name
        assert updated_lead.status == original_status

    @pytest.mark.asyncio
    async def test_update_lead_with_null_values(self, db_session: AsyncSession, sample_lead: Lead):
        """Test that null values in AI data don't update fields."""
        original_name = sample_lead.name

        ai_data = {
            "name": None,
            "phone": "201999999999"
        }
        updated_lead = await update_lead_from_ai(db_session, sample_lead.id, ai_data)
        await db_session.commit()

        # Name should not change, phone should update
        assert updated_lead.name == original_name
        assert updated_lead.phone == "201999999999"

    @pytest.mark.asyncio
    async def test_classify_lead(self, db_session: AsyncSession, sample_lead: Lead):
        """Test classifying lead directly."""
        updated_lead = await classify_lead(db_session, sample_lead.id, "warm")
        await db_session.commit()

        assert updated_lead is not None
        assert updated_lead.status == LeadStatus.WARM

    @pytest.mark.asyncio
    async def test_classify_lead_invalid_classification(self, db_session: AsyncSession, sample_lead: Lead):
        """Test that invalid classification doesn't crash."""
        original_status = sample_lead.status

        updated_lead = await classify_lead(db_session, sample_lead.id, "invalid_status")
        await db_session.commit()

        # Status should not change
        assert updated_lead.status == original_status

    @pytest.mark.asyncio
    async def test_get_lead_by_id(self, db_session: AsyncSession, sample_lead: Lead):
        """Test getting lead by ID."""
        retrieved_lead = await get_lead_by_id(db_session, sample_lead.id)

        assert retrieved_lead is not None
        assert retrieved_lead.id == sample_lead.id
        assert retrieved_lead.platform_sender_id == sample_lead.platform_sender_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_lead_returns_none(self, db_session: AsyncSession):
        """Test that getting a non-existent lead returns None."""
        from uuid import uuid4

        fake_id = uuid4()
        lead = await get_lead_by_id(db_session, fake_id)

        assert lead is None

    @pytest.mark.asyncio
    async def test_update_nonexistent_lead_returns_none(self, db_session: AsyncSession):
        """Test that updating a non-existent lead returns None."""
        from uuid import uuid4

        fake_id = uuid4()
        ai_data = {"name": "Test"}

        result = await update_lead_from_ai(db_session, fake_id, ai_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_different_platforms_different_leads(self, db_session: AsyncSession):
        """Test that same sender_id on different platforms creates different leads."""
        sender_id = "201333333333"

        lead_whatsapp = await get_or_create_lead(db_session, "whatsapp", sender_id)
        await db_session.commit()

        lead_messenger = await get_or_create_lead(db_session, "messenger", sender_id)
        await db_session.commit()

        # Should be different leads
        assert lead_whatsapp.id != lead_messenger.id
        assert lead_whatsapp.platform == Platform.WHATSAPP
        assert lead_messenger.platform == Platform.MESSENGER

    @pytest.mark.asyncio
    async def test_classification_mapping(self, db_session: AsyncSession, sample_lead: Lead):
        """Test all classification mappings work correctly."""
        classifications = [
            ("hot", LeadStatus.HOT),
            ("warm", LeadStatus.WARM),
            ("cold", LeadStatus.COLD),
            ("converted", LeadStatus.CONVERTED),
            ("lost", LeadStatus.LOST),
        ]

        for classification, expected_status in classifications:
            ai_data = {"classification": classification}
            updated_lead = await update_lead_from_ai(db_session, sample_lead.id, ai_data)
            await db_session.commit()

            assert updated_lead.status == expected_status, f"Failed for {classification}"
