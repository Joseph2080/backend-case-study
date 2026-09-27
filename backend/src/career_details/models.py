from datetime import datetime
from typing import ClassVar
from uuid import UUID, uuid4

from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel

from src.db.mixins import utc_created_at_field, utc_updated_at_field


class WorkExperienceModel(SQLModel, table=True):
    """Stable identity for one person's role within a user account."""

    __tablename__: ClassVar[str] = "work_experiences"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True)

    created_at: datetime = utc_created_at_field()
    updated_at: datetime = utc_updated_at_field()


class CareerDetailsModel(SQLModel, table=True):
    __tablename__: ClassVar[str] = "career_details"

    work_experience_id: UUID = Field(primary_key=True, foreign_key="work_experiences.id", ondelete="CASCADE")

    annual_salary: int = Field(sa_type=BigInteger)
    salary_currency: str = Field(max_length=3)
    weekly_hours: int
    direct_reports: int

    created_at: datetime = utc_created_at_field()
    updated_at: datetime = utc_updated_at_field()
