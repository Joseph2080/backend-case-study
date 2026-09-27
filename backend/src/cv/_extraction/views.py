from __future__ import annotations

from datetime import date
from typing import Literal, NotRequired, TypedDict

from pydantic import BaseModel, Field

from src.cv.views.cv_data import LanguageLevel, SkillLevel
from src.utils.supported_language import SupportedLanguage
from src.utils.utils import literal_to_list


class ExactDate(BaseModel):
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1900, le=2100)

    @property
    def date(self) -> date:
        return date(year=self.year, month=self.month, day=self.day)

    def to_string(self) -> str:
        return f"{self.day}.{self.month}.{self.year}"


class ApproximateDate(BaseModel):
    month: int | None = Field(ge=1, le=12, default=None, description="Leave empty (i.e. `null`) if not explicitly stated.")
    year: int = Field(ge=1900, le=2100)


class CVExtractedData(BaseModel):
    is_cv: bool = Field(description="Whether the document is even a CV.")
    language: SupportedLanguage | None = Field(
        description=f"The language of the CV. If not one of {literal_to_list(SupportedLanguage)}, leave empty (i.e. `null`)."
    )
    personal_details: PersonalDetails = Field(description="The personal details of the CV.")
    professional_summary: ProfessionalSummary | None

    sections: list[
        SocialLinksSection
        | EmploymentHistorySection
        | EducationSection
        | SkillsSection
        | LanguagesSection
        | AwardsSection
        | ExtraCurricularActivitiesSection
        | CoursesSection
        | HobbiesSection
        | ReferencesSection
        | PrivacyClauseSection
        | CustomSection
    ] = Field(description="All CV sections in the **exact order** they appear in the document.")

    class PersonalDetails(BaseModel):
        first_name: str
        last_name: str
        professional_title: str | None = Field(
            description="A professional title/headline visually displayed as part of the header, directly below or "
            "beside the person's name. Leave null if not present in header—do not infer from other CV sections."
        )
        email: str | None
        phone: str | None
        street_address: str | None = Field(description="Just the street name and number (no city, state, or zip code)")
        city: str | None
        state: str | None = Field(description="Only if explicitly stated in the CV.")
        postal_code: str | None
        country: str | None
        date_of_birth: ExactDate | None
        driving_license: str | None
        place_of_birth: str | None
        nationality: str | None
        personal_website: str | None

    class ProfessionalSummary(BaseModel):
        summary: str = Field(description="Sentences that describe the person. Only fill if this is 1-to-1 on the CV.")

    # Section wrapper classes with discriminator
    class SocialLinksSection(BaseModel):
        kind: Literal["social_links"] = "social_links"
        social_links: list[Item] = Field(description="Every social link the person has on their CV (only if url is known).")

        class Item(BaseModel):
            label: str
            url: str

    class EmploymentHistorySection(BaseModel):
        kind: Literal["employment"] = "employment"
        employment: list[Item] = Field(description="Every employer the person has worked for.")

        class Item(BaseModel):
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            job_title: str | None
            employer: str | None
            city: str | None
            description: str | None = Field(description="Use HTML formatting")

    class EducationSection(BaseModel):
        kind: Literal["education"] = "education"
        education: list[Item] = Field(description="Every education the person has attended.")

        class Item(BaseModel):
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            school_name: str | None
            degree: str | None
            city: str | None
            description: str | None = Field(description="Use HTML formatting")

    class SkillsSection(BaseModel):
        kind: Literal["skills"] = "skills"
        groups: list[SkillGroup] = Field(
            description="Skills organized by group. If skills are ungrouped in the CV, use a single group with name=null."
        )

        class SkillGroup(BaseModel):
            name: str | None = Field(description="Group name (e.g., 'IT-Kenntnisse', 'Soft Skills'), or null if ungrouped.")
            skills: list[Item]

            class Item(BaseModel):
                skill_name: str
                level: SkillLevel | None

    class LanguagesSection(BaseModel):
        kind: Literal["languages"] = "languages"
        languages: list[Item] = Field(description="Every language the person speaks according to the CV.")

        class Item(BaseModel):
            language: str
            level: LanguageLevel | None

    class AwardsSection(BaseModel):
        kind: Literal["awards"] = "awards"
        awards: list[Item] = Field(description="Every award the person has received.")

        class Item(BaseModel):
            name: str = Field(description="Activity name, job title, book title, etc.")
            city: str | None
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            description: str | None = Field(description="Use HTML formatting")

    class ExtraCurricularActivitiesSection(BaseModel):
        kind: Literal["extracurricular"] = "extracurricular"
        extra_curricular_activities: list[Item] = Field(description="Every extra-curricular activity the person has participated in.")

        class Item(BaseModel):
            function_title: str
            employer: str | None
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            city: str | None
            description: str | None = Field(description="Use HTML formatting")

    class CoursesSection(BaseModel):
        kind: Literal["courses"] = "courses"
        courses: list[Item]

        class Item(BaseModel):
            course: str
            institution: str | None
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None

    class HobbiesSection(BaseModel):
        kind: Literal["hobbies"] = "hobbies"
        hobbies: list[str]

    class ReferencesSection(BaseModel):
        kind: Literal["references"] = "references"
        references: list[Item]

        class Item(BaseModel):
            referent_full_name: str = Field(description="Full name of the referent.")
            company_name: str | None
            phone: str | None
            email: str | None

    class PrivacyClauseSection(BaseModel):
        kind: Literal["privacy_clause"] = "privacy_clause"
        text: str = Field(description="The privacy clause as written in the CV.")

    class CustomSection(BaseModel):
        kind: Literal["custom"] = "custom"
        title: str = Field(description="Title of the section")
        content: str | list[Item]

        class Item(BaseModel):
            title: str
            start_date: ApproximateDate | None
            end_date: ApproximateDate | None
            city: str | None
            description: str | None = Field(description="Use HTML formatting")


# region: - Validation errors


class ExtractionValidationError(TypedDict):
    error: str  # required
    resolution_hint: NotRequired[str]


# endregion
