import uuid
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

from src.db.mixins import utc_created_at_field, utc_updated_at_field

if TYPE_CHECKING:  # pragma: no cover - for type checking only, avoids import cycles at runtime
    from src.cv.models.cv_section import CVSectionModel


class CVItemModel(SQLModel, table=True):
    __tablename__: ClassVar[str] = "cv_items"
    __table_args__ = (
        # Ensure unique position per section (deferrable to allow position swapping)
        UniqueConstraint("section_id", "position", name="unique_item_position_per_section", deferrable=True, initially="DEFERRED"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Relationships
    section_id: uuid.UUID = Field(foreign_key="cv_sections.id", ondelete="CASCADE", index=True)
    section: Mapped["CVSectionModel"] = Relationship(back_populates="items")

    # Order position of this item in the section
    position: int = Field(default=0, description="Order position of this item in the section")

    # Shared career-details identity for employment entries (null for other section types)
    work_experience_id: uuid.UUID | None = Field(default=None, foreign_key="work_experiences.id", ondelete="SET NULL", index=True)

    # Generic columns that map to different section types:
    # employment:  title=job_title,        organization=employer
    # education:   title=degree,           organization=school_name
    # award:       title=name,             organization=None
    # course:      title=course,           organization=institution
    # extracurricular: title=function_title, organization=employer
    # custom: title=item.title, etc.
    title: str | None = Field(default=None)
    organization: str | None = Field(default=None)
    city: str | None = Field(default=None)
    description: str | None = Field(default=None)

    start_year: int | None = Field(default=None)
    start_month: int | None = Field(default=None, ge=1, le=12)
    end_year: int | None = Field(default=None)
    end_month: int | None = Field(default=None, ge=1, le=12)

    created_at: datetime = utc_created_at_field()
    updated_at: datetime = utc_updated_at_field()

    # - Helpers

    def with_position(self, position: int) -> "CVItemModel":
        self.position = position
        return self
