import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

from src.db.mixins import utc_created_at_field, utc_updated_at_field

if TYPE_CHECKING:  # pragma: no cover - for type checking only, avoids import cycles at runtime
    from src.cv.models.cv import CVModel
    from src.cv.models.cv_attribute import CVAttributeModel
    from src.cv.models.cv_item import CVItemModel


class CVSectionType(str, Enum):
    employment = "employment"
    education = "education"
    skills = "skills"
    languages = "languages"
    awards = "awards"
    hobbies = "hobbies"
    references = "references"
    social_links = "social_links"
    courses = "courses"
    extracurricular = "extracurricular"
    custom = "custom"


class CVSectionModel(SQLModel, table=True):
    __tablename__: ClassVar[str] = "cv_sections"
    __table_args__ = (
        # Ensure unique position per CV (deferrable to allow position swapping)
        UniqueConstraint("cv_id", "position", name="unique_position_per_cv", deferrable=True, initially="DEFERRED"),
        # Only enforce uniqueness for non-custom section types (using partial unique index)
        Index("ix_unique_standard_section_per_cv", "cv_id", "type", unique=True, postgresql_where=text("type != 'custom'")),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Relationships
    cv_id: uuid.UUID = Field(foreign_key="cvs.id", ondelete="CASCADE")
    cv: "CVModel" = Relationship(back_populates="sections")

    # Section metadata
    type: CVSectionType
    title: str | None = None  # Required for custom sections, ignored for standard sections
    position: int = Field(description="Order position of this section in the CV")

    # For sections with simple text content (professional_summary, some custom sections)
    text_content: str | None = None

    # Relationships to content (auto-ordered by position)
    items: Mapped[list["CVItemModel"]] = Relationship(
        back_populates="section", cascade_delete=True, sa_relationship_kwargs={"order_by": "CVItemModel.position"}
    )
    attributes: Mapped[list["CVAttributeModel"]] = Relationship(
        back_populates="section", cascade_delete=True, sa_relationship_kwargs={"order_by": "CVAttributeModel.position"}
    )

    created_at: datetime = utc_created_at_field()
    updated_at: datetime = utc_updated_at_field()
