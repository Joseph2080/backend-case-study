import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

from src.db.mixins import utc_created_at_field, utc_updated_at_field

if TYPE_CHECKING:  # pragma: no cover - for type checking only, avoids import cycles at runtime
    from src.cv.models.cv_section import CVSectionModel


class CVAttributeSkillLevel(str, Enum):
    novice = "novice"
    beginner = "beginner"
    skillful = "skillful"
    experienced = "experienced"
    expert = "expert"


class CVAttributeLanguageLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    basic = "basic"
    elementary = "elementary"
    intermediate = "intermediate"
    advanced = "advanced"
    fluent = "fluent"
    native = "native"
    conversational = "conversational"
    professional = "professional"


class CVAttributeModel(SQLModel, table=True):
    __tablename__: ClassVar[str] = "cv_attributes"
    __table_args__ = (
        # Ensure unique position per section (deferrable to allow position swapping)
        UniqueConstraint("section_id", "position", name="unique_attribute_position_per_section", deferrable=True, initially="DEFERRED"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Relationships
    section_id: uuid.UUID = Field(foreign_key="cv_sections.id", ondelete="CASCADE", index=True)
    section: Mapped["CVSectionModel"] = Relationship(back_populates="attributes")

    # Order position of this attribute in the section
    position: int = Field(default=0, description="Order position of this attribute in the section")

    # Common "name" field, usage depends on section type:
    #  - skills:       name = skill_name
    #  - languages:    name = language
    #  - hobbies:      name = hobby text
    #  - references:   name = referent_full_name
    #  - social_links: name = label
    #  - personal_details: name = field_name (e.g., "first_name", "email", etc.)
    name: str = Field(...)

    # For personal_details section - stores the value of the field
    value: str | None = Field(default=None)

    # Levels (one of these will be used depending on kind)
    skill_level: CVAttributeSkillLevel | None = Field(default=None)
    language_level: CVAttributeLanguageLevel | None = Field(default=None)

    # For skills
    skill_group_name: str | None = Field(default=None)

    # For references
    company_name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)

    # For links
    url: str | None = Field(default=None)

    created_at: datetime = utc_created_at_field()
    updated_at: datetime = utc_updated_at_field()

    # - Helpers

    def with_position(self, position: int) -> "CVAttributeModel":
        self.position = position
        return self
