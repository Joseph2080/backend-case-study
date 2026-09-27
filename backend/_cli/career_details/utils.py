from uuid import UUID

from fastapi import HTTPException
from rich.console import Console
from rich.table import Table

from src.career_details.service import CareerDetailsService
from src.career_details.views import CareerDetails
from src.cv.service import CVService
from src.cv.views.cv_data import ApproximateDate, CVData


async def show_employment_details(cv_id: UUID, user_id: str) -> list[tuple[CVData.EmploymentHistorySection.Item, CareerDetails | None]]:
    cv = await CVService().get_cv_by_id(cv_id, user_id)
    if cv is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    career_details_service = CareerDetailsService()
    console = Console(markup=False)
    console.print(f"{cv.cv_name or 'CV'} ({cv.id})", markup=False)
    table = Table()
    for heading in ("#", "Employer", "Role", "Dates", "Annual salary", "Hours/week", "Direct reports"):
        table.add_column(heading)
    rows: list[tuple[CVData.EmploymentHistorySection.Item, CareerDetails | None]] = []
    for section in cv.sections:
        if not isinstance(section, CVData.EmploymentHistorySection):
            continue
        for item in section.employment:
            details = await career_details_service.get_details(item.id, user_id)
            rows.append((item, details))
            table.add_row(
                str(len(rows)),
                item.employer or "-",
                item.job_title or "-",
                f"{_format_date(item.start_date)} - {_format_date(item.end_date)}",
                f"{details.annual_salary:,} {details.salary_currency}" if details else "Not entered",
                str(details.weekly_hours) if details else "-",
                str(details.direct_reports) if details else "-",
            )
    console.print(table)
    if not rows:
        console.print("This CV has no employment entries.")
    return rows


def _format_date(value: ApproximateDate | None) -> str:
    if value is None:
        return "?"
    return f"{value.month:02d}/{value.year}" if value.month is not None else str(value.year)
