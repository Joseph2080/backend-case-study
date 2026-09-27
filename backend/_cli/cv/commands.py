from _cli.base import AsyncTyper
from _cli.cv.duplicate_cv import duplicate_cv
from _cli.cv.import_cv import import_cv
from _cli.cv.list_cvs import list_cvs

app = AsyncTyper(no_args_is_help=True)
app.add_command(list_cvs, name="list")
app.add_command(import_cv, name="import")
app.add_command(duplicate_cv, name="duplicate")
