from typing import Any, Callable, Coroutine, Literal, Protocol, TypeVar, cast, get_args, get_origin

from fastapi import params

T = TypeVar("T")


def literal_to_list(literal: object) -> list[Any]:
    values: list[Any] = []
    for arg in get_args(literal):
        if get_origin(arg) is Literal:
            values.extend(literal_to_list(arg))
        else:
            values.append(arg)
    return values


class Identifiable(Protocol[T]):
    id: T


Identifiable_T = TypeVar("Identifiable_T", bound=Identifiable)


def dedup_identifiable_sorted_items(items: list[Identifiable_T]) -> list[Identifiable_T]:
    seen = set()
    output: list[Identifiable_T] = []
    for item in items:
        if item.id in seen:
            continue
        seen.add(item.id)
        output.append(item)
    return output


def SafeDepends(dependency: Callable[..., Coroutine[Any, Any, T]], *, use_cache: bool = True) -> T:  # noqa: N802
    # @dev only works for class methods I think
    return cast(T, params.Depends(dependency=dependency, use_cache=use_cache))
