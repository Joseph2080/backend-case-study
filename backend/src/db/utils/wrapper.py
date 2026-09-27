from functools import wraps
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, Protocol, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.service import DatabaseService

P = ParamSpec("P")
R = TypeVar("R")


class _DBServiceIntegrated(Protocol):
    db_service: DatabaseService


_DBServiceIntegratedInstance = TypeVar("_DBServiceIntegratedInstance", bound=_DBServiceIntegrated)


def with_database_session(
    func: Callable[Concatenate[_DBServiceIntegratedInstance, AsyncSession, P], Coroutine[Any, Any, R]],
) -> Callable[Concatenate[_DBServiceIntegratedInstance, P], Coroutine[Any, Any, R]]:
    """
    Decorator to inject a database session into a function.

    @dev This decorator should be used on a class method of a class that has a `db_service` attribute.
    """

    @wraps(func)
    async def wrapper(instance: _DBServiceIntegratedInstance, *args: P.args, **kwargs: P.kwargs) -> R:
        async with await instance.db_service.get_session() as session:
            return await func(instance, session, *args, **kwargs)

    return wrapper
