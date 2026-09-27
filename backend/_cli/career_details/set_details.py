from uuid import UUID

import click
import typer
from _cli.career_details.utils import show_employment_details

from src.career_details.service import CareerDetailsService
from src.career_details.views import CareerDetails


async def set_details(
    cv_id: UUID = typer.Argument(..., help="CV containing the employment entry to edit."),
    user: str = typer.Option("alice", help="Local user ID, e.g. alice or bob."),
):
    """Select an employment entry and enter or edit its private career details."""
    rows = await show_employment_details(cv_id, user)
    if not rows:
        raise typer.Exit(code=1)
    selection: int = typer.prompt("Employment number", type=click.IntRange(1, len(rows)))
    item, existing = rows[selection - 1]
    annual_salary: int = typer.prompt(
        "Annual base salary", type=click.IntRange(min=0), default=existing.annual_salary if existing else None
    )
    salary_currency: str = typer.prompt("Currency (e.g. CHF)", default=existing.salary_currency if existing else None)
    weekly_hours: int = typer.prompt("Weekly hours", type=click.IntRange(0, 168), default=existing.weekly_hours if existing else None)
    direct_reports: int = typer.prompt("Direct reports", type=click.IntRange(min=0), default=existing.direct_reports if existing else None)
    request = CareerDetails(
        annual_salary=annual_salary,
        salary_currency=salary_currency.strip().upper(),
        weekly_hours=weekly_hours,
        direct_reports=direct_reports,
    )
    await CareerDetailsService().update_details(item.id, request, user)
    typer.echo("Career details saved.")
