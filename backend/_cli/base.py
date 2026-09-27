import asyncio
from functools import wraps

import typer
from typer import Typer


class AsyncTyper(Typer):
    def add_command(self, f, confirmation_prompt=False, *, name: str | None = None):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not asyncio.iscoroutinefunction(f):
                return f(*args, **kwargs)

            if confirmation_prompt:
                print("\n###############################################")
                print(f"Running {f.__name__} with args {args} and kwargs {kwargs}")
                print("###############################################\n")
                typer.confirm("Press enter to continue...", abort=True)
            return asyncio.run(f(*args, **kwargs))

        self.command(name=name)(wrapper)
