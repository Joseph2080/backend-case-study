- After finishing up work in backend, always make sure that the types are all correct with `uv run pyright`
- If adding packages, try to always add them via `uv add <package_name>` instead of directly in the `pyproject.toml`
- For testing, you can start normally with `uv run server.py`. If it says that the "address is already in use", the user has likely an instance running on their own. Ask them to stop it. And then try again.
- In FastAPI, avoid returning a dict for a success or error response. Instead, use either a pydantic model or just let the status code handle it, i.e. don't return anything.
- Don't use imports within functions. Instead, import at the top of the file. Only exception is to prevent circular imports.
- All `uv` commands should be run from the "backend/" directory.
- This backend code should be as type-safe as possible. That means that when we change types or functions or other code in the future, which violates assumed contracts, it should be caught by the type checker.
- When possible, make match statements exhaustive and avoid wildcard arms. (part of effort to make it type-safe)
- Don't put types, functions, or anything other than imports, logging setup, and (only if strictly necessary) module-level constants on top of service.py files.
- Database SQL migrations belong in `src/db/migrations/`. Name new database SQL migrations with the next zero-padded numeric prefix - as the others.

## Backend File Structure

- Keep backend source under `src/<feature>/` unless it is CLI-only (`_cli/`), a DB migration (`src/db/migrations/`), middleware, or shared infrastructure.
- Feature-owned internal subfeatures must be underscore-prefixed folders, for example `_rendering`, `_tailoring`, `_recommendation_api`, or `_r2`.
- Allowed feature-level filenames are `router.py`, `service.py`, `views.py` or `views/`, `models.py` or `models/`, `utils.py`, `prompts.py` or `prompts/`, and `localization.py`. Different filenames need explicit consent from the user.
- Do not invent vague filenames like `helpers.py`, `common.py`, `manager.py`, `handler.py`, or `processor.py`. Put the code in the existing `service.py`, `utils.py`, `views.py`, or a specifically named private subfeature.
- Keep route handlers in `router.py`, business logic in `service.py`, API contracts in `views.py` or `views/`, SQLModel/database shapes in `models.py` or `models/`, and small pure helpers in `utils.py`.
- Start with a single `views.py`, `models.py`, or `prompts.py`. Split into a folder only when the file is clearly becoming hard to scan or has multiple independent contracts; then use focused filenames like `requests.py`, `responses.py`, `cv_data.py`, or `analytics_responses.py` (no restrictions apply there).
- For `_cli`, each command group gets a `commands.py` aggregator, and each real command gets its own focused file.

## General Rules

- Do not remove existing documentation/comments unless explicitly asked.
- When in a *py file:
  - Always use modern typehints (Python 3.10+), i.e. `list` (not List), `X | None` (not `Optional[X]`) etc.
  - For functions that return no value, don't do any type hints for the return type (not `-> None`)
  - Put all import on top of the file (not inside the function), except if strictly necessary or there is a clear benefit of doing it
  - Prefer f-strings for string interpolation whenever possible.
  - Never use `# type: ignore`; fix the type issue instead.
  - Don't use `__init__.py` files in normal non-library projects if not strictly necessary or explicitly asked by the user.
