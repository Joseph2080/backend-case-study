from __future__ import annotations

import json
from datetime import date
from typing import Annotated, Literal, TypeAlias
from uuid import UUID

from pydantic import BaseModel, Field

from src.cv.views.style import CVDatePosition, CVFontFamily, CVTextAlignment
from src.utils.country_code import CountryCode
from src.utils.supported_language import SupportedLanguage
from src.utils.types import HexColor

# Type aliases for skill and language levels - single source of truth
SkillLevel = Literal["novice", "beginner", "skillful", "experienced", "expert"]
# fmt: off
LanguageLevel = Literal[
    "A1", "A2", "B1", "B2", "C1", "C2",
    "basic", "elementary", "intermediate", "advanced", "fluent", "native", "conversational", "professional"
]
# fmt: on


class ApproximateDate(BaseModel):
    month: int | None = Field(ge=1, le=12)
    year: int = Field(ge=1900, le=2100)


class CVData(BaseModel):
    id: UUID
    cv_name: str | None
    cv_language: SupportedLanguage
    target_country_code: CountryCode | None
    style: Style
    personal_details: PersonalDetails
    # social_links: list[SocialLinkItem]
    professional_summary: ProfessionalSummary | None
    # employment: list[EmploymentHistoryItem]
    # education: list[EducationItem]
    # skills: list[SkillItem]
    # languages: list[LanguageItem]
    # awards: list[AwardItem]
    # extra_curricular_activities: list[ExtraCurricularActivityItem]
    # courses: list[CourseItem]
    # # internships: list[EmploymentHistoryItem]  # currently handled as employment history
    # hobbies: list[str]
    # references: list[ReferenceItem]
    # custom_sections: list[CustomSection]

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
    footer_sections: FooterSections

    def to_llm_json(self) -> str:
        """Serialize CVData for LLM prompts, excluding metadata fields that provide no value."""
        data = self.model_dump(mode="json", exclude={"id"})

        # PrivacyClause is an empty persistence marker, so expose its enabled state explicitly only to the LLM (to not confuse it).
        if data["footer_sections"]["privacy_clause"] is not None:
            data["footer_sections"]["privacy_clause"] = {"enabled": True}

        return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    class Style(BaseModel):
        template_id: str
        accent_color: HexColor | None

        section_spacing: float = Field(default=1.0, ge=0.7, le=1.3)
        line_spacing: float = Field(default=1.0, ge=0.7, le=1.3)
        margin_spacing: float = Field(default=1.0, ge=0.7, le=1.3)
        date_position: CVDatePosition | None = None
        text_alignment: CVTextAlignment | None = None

        font_size: float = Field(default=1.0, ge=0.7, le=1.3)
        font_family: CVFontFamily | None = None
        content_font_scale: float = Field(default=1.0, ge=0.7, le=1.4)
        heading_font_scale: float = Field(default=1.0, ge=0.7, le=1.4)

    class FooterSections(BaseModel):
        """Final in-flow CV sections rendered in a fixed order."""

        privacy_clause: PrivacyClause | None
        signature: Signature | None

        class PrivacyClause(BaseModel):
            """Marks the auto-generated country-specific privacy clause section."""

        class Signature(BaseModel):
            location: str | None
            include_date: bool
            show_name: bool

    class PersonalDetails(BaseModel):
        first_name: str
        last_name: str
        professional_title: str | None

        email: str | None
        phone: str | None

        street_address: str | None
        city: str | None
        state: str | None
        postal_code: str | None
        country: str | None

        date_of_birth: date | None
        place_of_birth: str | None
        nationality: str | None
        marital_status: str | None

        driving_license: str | None
        personal_website: str | None

    class ProfessionalSummary(BaseModel):
        summary: str

    class SectionBase(BaseModel):
        id: UUID

    class SocialLinkSection(SectionBase):
        kind: Literal["social_links"] = "social_links"
        social_links: list[Item]

        class Item(BaseModel):
            id: UUID
            label: str
            url: str

    class EmploymentHistorySection(SectionBase):
        kind: Literal["employment"] = "employment"
        employment: list[Item]

        class Item(BaseModel):
            id: UUID
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            job_title: str | None
            employer: str | None
            city: str | None
            description: str | None

    class EducationSection(SectionBase):
        kind: Literal["education"] = "education"
        education: list[Item]

        class Item(BaseModel):
            id: UUID
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            school_name: str | None
            degree: str | None
            city: str | None
            description: str | None

    class SkillsSection(SectionBase):
        kind: Literal["skills"] = "skills"
        groups: list[SkillGroup]

        class SkillGroup(BaseModel):
            name: str | None  # None = ungrouped/default group, name is unique
            skills: list[Item]

            class Item(BaseModel):
                id: UUID
                skill_name: str
                level: SkillLevel | None

    class LanguagesSection(SectionBase):
        kind: Literal["languages"] = "languages"
        languages: list[Item]

        class Item(BaseModel):
            id: UUID
            language: str
            level: LanguageLevel | None

    class AwardsSection(SectionBase):
        kind: Literal["awards"] = "awards"
        awards: list[Item]

        class Item(BaseModel):
            id: UUID
            name: str
            city: str | None
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            description: str | None

    class ExtraCurricularActivitiesSection(SectionBase):
        kind: Literal["extracurricular"] = "extracurricular"
        extra_curricular_activities: list[Item]

        class Item(BaseModel):
            id: UUID
            function_title: str
            employer: str | None
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            city: str | None
            description: str | None

    class CoursesSection(SectionBase):
        kind: Literal["courses"] = "courses"
        courses: list[Item]

        class Item(BaseModel):
            id: UUID
            course: str
            institution: str | None
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None

    class HobbiesSection(SectionBase):
        kind: Literal["hobbies"] = "hobbies"
        hobbies: list[Item]

        class Item(BaseModel):
            id: UUID
            hobby: str

    class ReferencesSection(SectionBase):
        kind: Literal["references"] = "references"
        references: list[Item]

        class Item(BaseModel):
            id: UUID
            referent_full_name: str
            company_name: str | None
            phone: str | None
            email: str | None

    class CustomSection(SectionBase):
        kind: Literal["custom"] = "custom"
        title: str
        content: str | list[ContentItem]

        class ContentItem(BaseModel):
            id: UUID
            title: str
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            city: str | None
            description: str | None


# -------


# Shared union of all supported CV sections (for using outside of this file)
CVDataSectionType: TypeAlias = Annotated[
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
    | CVData.CustomSection,
    Field(discriminator="kind"),
]
