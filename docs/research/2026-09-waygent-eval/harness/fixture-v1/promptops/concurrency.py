"""Shared concurrency helper. Use this instead of hand-rolled semaphores."""
import asyncio
from typing import Awaitable, Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


async def gather_limited(items: Iterable[T], fn: Callable[[T], Awaitable[R]], limit: int) -> list[tuple[T, R | BaseException]]:
    """Run fn(item) for every item with at most `limit` running at once.

    Returns (item, result or exception) in input order. One item's exception does not
    stop the others. Cancelling the awaiting task cancels every pending and running call.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    sem = asyncio.Semaphore(limit)

    async def one(item):
        async with sem:
            return await fn(item)

    items = list(items)
    tasks = [asyncio.ensure_future(one(i)) for i in items]
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    return list(zip(items, results))
