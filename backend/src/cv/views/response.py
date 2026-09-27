from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.cv.views.cv_data import CVData
from src.utils.country_code import CountryCode
from src.utils.supported_language import SupportedLanguage


class FullCVContent(BaseModel):
    id: UUID
    cv_name: str | None
    cv_language: SupportedLanguage
    style: CVData.Style
    personal_details: CVData.PersonalDetails
    professional_summary: CVData.ProfessionalSummary | None
    footer_sections: CVData.FooterSections

    # should be in-sync with `CVData.sections`
    sections: list[
        Annotated[
            CVData.SocialLinkSection
            | CVData.EmploymentHistorySection
            | CVData.EducationSection
            | CVData.SkillsSection
            | CVData.LanguagesSection
            | CVData.AwardsSection
            | CVData.ExtraCurricularActivitiesSection
            | CVData.CoursesSection
            | CVData.HobbiesSection
            | CVData.ReferencesSection
            | CustomSection,
            Field(discriminator="kind"),
        ]
    ]

    class CustomSection(CVData.CustomSection):
        content: Annotated[TextContent | StructuredContent, Field(discriminator="content_type")]

        class TextContent(BaseModel):
            content_type: Literal["text"] = "text"
            text: str

        class StructuredContent(BaseModel):
            content_type: Literal["structured"] = "structured"
            items: list[CVData.CustomSection.ContentItem]


class CVListItemResponse(BaseModel):
    """Lightweight CV response for list views."""

    id: UUID
    cv_name: str | None
    first_name: str
    last_name: str
    email: str | None
    created_at: datetime
    updated_at: datetime


class CVTargetCountryResponse(BaseModel):
    target_country_code: CountryCode | None
