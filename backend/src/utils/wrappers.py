import asyncio
import random
from logging import Logger
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class RetryExhaustedError(Exception):
    def __init__(self, max_retries: int, last_error: Exception):
        self.max_retries = max_retries
        self.last_error = last_error
        super().__init__(f"Maximum number of retries ({max_retries}) exceeded.")


def retry_with_exponential_backoff_async(
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 20,
    max_delay: float = 180,
    errors: tuple = (Exception,),
    log_on_retry: Logger | None = None,
):
    """
    Retry a function with exponential backoff.

    @param log_on_retry: If set, logs the error message on each retry to the specified logger
    """

    def decorator(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Coroutine[Any, Any, R]]:
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            num_retries = 0
            delay = initial_delay

            while True:
                try:
                    return await func(*args, **kwargs)
                except errors as e:
                    num_retries += 1

                    if log_on_retry:
                        log_on_retry.info(f"Retrying ({num_retries}) {func.__name__} due to error {e.__class__.__name__}: {e}")

                    if num_retries > max_retries:
                        raise RetryExhaustedError(max_retries=max_retries, last_error=e) from e

                    delay *= exponential_base * (1 + (random.random() if jitter else 0))
                    delay = min(delay, max_delay + (random.random() if jitter else 0))

                    await asyncio.sleep(delay)
                except Exception as e:
                    raise e

        return wrapper

    return decorator
