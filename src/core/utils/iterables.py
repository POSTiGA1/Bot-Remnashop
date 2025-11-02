from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def chunked(iterable: Iterable[T], size: int) -> list[list[T]]:
    chunk: list[T] = []
    result: list[list[T]] = []

    for item in iterable:
        chunk.append(item)

        if len(chunk) >= size:
            result.append(chunk)
            chunk = []

    if chunk:
        result.append(chunk)

    return result
