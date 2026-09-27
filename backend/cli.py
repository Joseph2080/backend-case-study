import logging

import typer
from _cli.career_details.commands import app as career_details_app
from _cli.cv.commands import app as cv_app
from fastapi import HTTPException
from pydantic import ValidationError

import src.db.models  # noqa: F401

logging.basicConfig(level=logging.WARNING)

app = typer.Typer(pretty_exceptions_enable=False, pretty_exceptions_show_locals=False, no_args_is_help=True)
app.add_typer(cv_app, name="cv")
app.add_typer(career_details_app, name="career-details")

if __name__ == "__main__":
    try:
        app()
    except (HTTPException, ValidationError, OSError) as error:
        message = str(error.detail) if isinstance(error, HTTPException) else str(error)
        typer.secho(message, fg=typer.colors.RED, err=True)
        raise SystemExit(1) from None
