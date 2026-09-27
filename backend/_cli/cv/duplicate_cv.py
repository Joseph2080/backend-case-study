from uuid import UUID

import typer
from fastapi import HTTPException

from src.cv.service import CVService


async def duplicate_cv(
    cv_id: UUID = typer.Argument(..., help="CV ID to duplicate."),
    user: str = typer.Option("alice", help="Local user ID, e.g. alice or bob."),
):
    """Duplicate a CV with fresh item IDs."""
    result = await CVService().duplicate_cv(cv_id, user)
    if result is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    typer.echo(f"Duplicated CV: {result.id}")
