import asyncio
import inspect
from functools import wraps
from typing import Any, Awaitable, Callable, Coroutine, Generic, Hashable, ParamSpec, TypeVar

Identifier = TypeVar("Identifier", bound=Hashable)
Input = ParamSpec("Input")
Output = TypeVar("Output")


class TaskGroup(Generic[Identifier, Input, Output]):
    """
    Task group that only allows one task per identifier to run at a time within a single worker,
    while sharing the result of the task.
    """

    def __init__(self, task_factory: Callable[Input, Awaitable[Output]], identifier_factory: Callable[Input, Identifier]):
        self.task_factory = task_factory
        self.identifier_factory = identifier_factory
        self.active_tasks: dict[Identifier, asyncio.Task[Output]] = {}
        self.task_lock = asyncio.Lock()

    async def run(self, *args: Input.args, **kwargs: Input.kwargs) -> Output:
        identifier = self.identifier_factory(*args, **kwargs)

        async def task_wrapper() -> Output:
            current_task = asyncio.current_task()
            try:
                return await self.task_factory(*args, **kwargs)
            finally:
                async with self.task_lock:
                    if self.active_tasks.get(identifier) is current_task:
                        del self.active_tasks[identifier]

        async with self.task_lock:
            if identifier in self.active_tasks:
                task = self.active_tasks[identifier]
            else:
                task = asyncio.create_task(task_wrapper())
                self.active_tasks[identifier] = task

        return await asyncio.shield(task)

    def run_in_background(self, *args: Input.args, **kwargs: Input.kwargs) -> asyncio.Task[Output]:
        return asyncio.create_task(self.run(*args, **kwargs))


def task_group(
    identifier: Callable[Input, Hashable],
) -> Callable[[Callable[Input, Coroutine[Any, Any, Output]]], Callable[Input, Coroutine[Any, Any, Output]]]:
    """
    Decorator to create a task group that only allows one task per identifier to run at a time
    within a single worker, while sharing the result of the task.
    """

    def decorator(func: Callable[Input, Coroutine[Any, Any, Output]]) -> Callable[Input, Coroutine[Any, Any, Output]]:
        task_group_instance = TaskGroup[Any, Input, Output](task_factory=func, identifier_factory=identifier)

        @wraps(func)
        async def wrapper(*args: Input.args, **kwargs: Input.kwargs) -> Output:
            return await task_group_instance.run(*args, **kwargs)

        return wrapper

    return decorator


def task_group_with_param(
    key: str,
) -> Callable[[Callable[Input, Coroutine[Any, Any, Output]]], Callable[Input, Coroutine[Any, Any, Output]]]:
    """
    Decorator like task_group but derive the identifier from a named parameter,
    preserving the original signature.
    """

    def decorator(func: Callable[Input, Coroutine[Any, Any, Output]]) -> Callable[Input, Coroutine[Any, Any, Output]]:
        signature = inspect.signature(func)
        if key not in signature.parameters:
            raise ValueError(f"Parameter '{key}' not found in function {func.__name__}")

        def identifier_factory(*args: Input.args, **kwargs: Input.kwargs) -> Hashable:
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            return bound.arguments[key]

        grouped = TaskGroup[Any, Input, Output](task_factory=func, identifier_factory=identifier_factory)

        @wraps(func)
        async def wrapper(*args: Input.args, **kwargs: Input.kwargs) -> Output:
            return await grouped.run(*args, **kwargs)

        return wrapper

    return decorator


def task_group_with_params(
    *keys: str,
) -> Callable[[Callable[Input, Coroutine[Any, Any, Output]]], Callable[Input, Coroutine[Any, Any, Output]]]:
    """
    Decorator like task_group but derive the identifier from multiple named parameters as a tuple.
    """

    def decorator(func: Callable[Input, Coroutine[Any, Any, Output]]) -> Callable[Input, Coroutine[Any, Any, Output]]:
        signature = inspect.signature(func)

        for key in keys:
            if key not in signature.parameters:
                raise ValueError(f"Parameter '{key}' not found in function {func.__name__}")

        def identifier_factory(*args: Input.args, **kwargs: Input.kwargs) -> Hashable:
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            return tuple(bound.arguments[key] for key in keys)

        grouped = TaskGroup[Any, Input, Output](task_factory=func, identifier_factory=identifier_factory)

        @wraps(func)
        async def wrapper(*args: Input.args, **kwargs: Input.kwargs) -> Output:
            return await grouped.run(*args, **kwargs)

        return wrapper

    return decorator
