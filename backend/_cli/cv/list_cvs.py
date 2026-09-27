import typer
from rich.console import Console
from rich.table import Table

from src.cv.service import CVService


async def list_cvs(user: str = typer.Option("alice", help="Local user ID, e.g. alice or bob.")):
    """List the selected user's CVs."""
    cvs = await CVService().list_cvs(user)
    console = Console(markup=False)
    table = Table(title=f"CVs for {user}")
    table.add_column("CV ID", no_wrap=True)
    table.add_column("Name")
    table.add_column("Person")
    for cv in cvs:
        table.add_row(str(cv.id), cv.cv_name or "CV", f"{cv.first_name} {cv.last_name}")
    console.print(table)
    if not cvs:
        console.print("No CVs yet. Import one with: uv run cli.py cv import PATH")
