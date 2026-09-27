from pathlib import Path

import typer
from fastapi import UploadFile
from starlette.datastructures import Headers

from src.cv.service import CVService
from src.cv.views.cv_data import CVData


async def import_cv(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="PDF or structured CVData JSON file."),
    user: str = typer.Option("alice", help="Local user ID, e.g. alice or bob."),
):
    """Import a JSON example or extract a PDF with OpenAI."""
    cv_service = CVService()
    match file.suffix.lower():
        case ".json":
            cv_data = CVData.model_validate_json(file.read_text())
            result = await cv_service.import_cv(cv_data, user)
        case ".pdf":
            typer.echo("Extracting PDF with OpenAI...")
            with file.open("rb") as stream:
                upload = UploadFile(file=stream, filename=file.name, headers=Headers({"content-type": "application/pdf"}))
                result = await cv_service.create_cv_from_upload(upload, user)
        case _:
            raise typer.BadParameter("Choose a .pdf or .json file.", param_hint="file")
    typer.echo(f"Imported CV: {result.id}")
