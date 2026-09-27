from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field


def utc_created_at_field():
    return Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


def utc_updated_at_field():
    return Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )


def utc_nullable_datetime_field():
    return Field(
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
