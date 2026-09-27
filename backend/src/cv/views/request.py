from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.cv.views.cv_data import CVData
from src.utils.country_code import CountryCode
from src.utils.supported_language import SupportedLanguage


class CreateEmptyCVRequest(BaseModel):
    language: SupportedLanguage


class UpdateCVTargetCountryRequest(BaseModel):
    target_country_code: CountryCode


class CVUpdateRequest(BaseModel):
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
            SocialLinkSection
            | EmploymentHistorySection
            | EducationSection
            | SkillsSection
            | LanguagesSection
            | AwardsSection
            | ExtraCurricularActivitiesSection
            | CoursesSection
            | HobbiesSection
            | ReferencesSection
            | CustomSection,
            Field(discriminator="kind"),
        ]
    ]

    class SocialLinkSection(CVData.SocialLinkSection):
        class Item(CVData.SocialLinkSection.Item):
            id: UUID | None

        id: UUID | None
        social_links: list[Item]

    class EmploymentHistorySection(CVData.EmploymentHistorySection):
        class Item(CVData.EmploymentHistorySection.Item):
            id: UUID | None

        id: UUID | None
        employment: list[Item]

    class EducationSection(CVData.EducationSection):
        class Item(CVData.EducationSection.Item):
            id: UUID | None

        id: UUID | None
        education: list[Item]

    class SkillsSection(CVData.SkillsSection):
        class SkillGroup(CVData.SkillsSection.SkillGroup):
            class Item(CVData.SkillsSection.SkillGroup.Item):
                id: UUID | None

            skills: list[Item]

        id: UUID | None
        groups: list[SkillGroup]

    class LanguagesSection(CVData.LanguagesSection):
        class Item(CVData.LanguagesSection.Item):
            id: UUID | None

        id: UUID | None
        languages: list[Item]

    class AwardsSection(CVData.AwardsSection):
        class Item(CVData.AwardsSection.Item):
            id: UUID | None

        id: UUID | None
        awards: list[Item]

    class ExtraCurricularActivitiesSection(CVData.ExtraCurricularActivitiesSection):
        class Item(CVData.ExtraCurricularActivitiesSection.Item):
            id: UUID | None

        id: UUID | None
        extra_curricular_activities: list[Item]

    class CoursesSection(CVData.CoursesSection):
        class Item(CVData.CoursesSection.Item):
            id: UUID | None

        id: UUID | None
        courses: list[Item]

    class HobbiesSection(CVData.HobbiesSection):
        class Item(CVData.HobbiesSection.Item):
            id: UUID | None

        id: UUID | None
        hobbies: list[Item]

    class ReferencesSection(CVData.ReferencesSection):
        class Item(CVData.ReferencesSection.Item):
            id: UUID | None

        id: UUID | None
        references: list[Item]

    class CustomSection(CVData.CustomSection):
        class TextContent(BaseModel):
            content_type: Literal["text"] = "text"
            text: str

        class StructuredContent(BaseModel):
            content_type: Literal["structured"] = "structured"
            items: list[ContentItem]

            class ContentItem(CVData.CustomSection.ContentItem):
                id: UUID | None

        id: UUID | None
        content: Annotated[TextContent | StructuredContent, Field(discriminator="content_type")]
