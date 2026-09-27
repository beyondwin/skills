"""Retry helper for transient failures. Use this; do not hand-roll retry loops."""
import asyncio


async def retry_async(fn, *, attempts: int = 3, base_delay: float = 0.01, retry_on=(Exception,)):
    """Call `await fn()` up to `attempts` times, sleeping base_delay * 2**i between tries.

    Only exceptions in `retry_on` are retried; anything else propagates at once.
    Cancellation always propagates immediately.
    """
    for i in range(attempts):
        try:
            return await fn()
        except retry_on:
            if i == attempts - 1:
                raise
            await asyncio.sleep(base_delay * 2 ** i)
