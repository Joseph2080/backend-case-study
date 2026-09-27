from _cli.base import AsyncTyper
from _cli.career_details.set_details import set_details
from _cli.career_details.show import show

app = AsyncTyper(no_args_is_help=True)
app.add_command(show)
app.add_command(set_details, name="set")
