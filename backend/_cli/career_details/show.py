from uuid import UUID

import typer
from _cli.career_details.utils import show_employment_details


async def show(
    cv_id: UUID = typer.Argument(..., help="CV whose employment details should be shown."),
    user: str = typer.Option("alice", help="Local user ID, e.g. alice or bob."),
):
    """Show private career details for every employment entry in a CV."""
    await show_employment_details(cv_id, user)
