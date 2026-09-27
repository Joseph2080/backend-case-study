from pydantic import BaseModel, Field


class CareerDetails(BaseModel):
    """Last known annual base salary, working hours, and direct reports for a work experience."""

    annual_salary: int = Field(ge=0, strict=True)
    salary_currency: str = Field(pattern=r"^[A-Z]{3}$")
    weekly_hours: int = Field(ge=0, le=168, strict=True)
    direct_reports: int = Field(ge=0, strict=True)
