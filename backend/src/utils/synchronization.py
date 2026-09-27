import asyncio
import functools
import inspect
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class param_synchronized:
    """
    Only allow one coroutine with the same given keyword argument to enter a method at a time across a single worker.
    """

    def __init__(self, key: str):
        """
        @param key: The keyword argument to use as the key for the lock
        """
        self.key = key
        self.locks: dict[Any, asyncio.Lock] = {}

    def __call__(self, func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        signature = inspect.signature(func)

        if self.key not in signature.parameters:
            raise ValueError(f"Keyword argument {self.key} defined in `@param_synchronized` not found in function {func}")

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            k = bound.arguments[self.key]

            if k not in self.locks:
                self.locks[k] = asyncio.Lock()
            async with self.locks[k]:
                return await func(*args, **kwargs)

        return wrapper
