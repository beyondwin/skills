"""Deterministic stand-in for the restyling model used in tests.

Bodies containing "REFUSE" are refused, bodies containing "BOOM" fail.
`on_call(model, body, style, model_name)` runs at the start of every call and may be async.
"""
import asyncio
import inspect


class ModelRefused(Exception):
    """The model declined to restyle this body."""


class ModelError(Exception):
    """The model call failed (timeout, 5xx, ...)."""


class FakeModel:
    def __init__(self, delay: float = 0.01, on_call=None):
        self.delay = delay
        self.on_call = on_call
        self.calls: list[tuple[str, str, str]] = []  # (body, style, model_name)
        self.active = 0
        self.peak = 0

    async def restyle(self, body: str, style: str, model_name: str) -> str:
        self.calls.append((body, style, model_name))
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            if self.on_call is not None:
                r = self.on_call(self, body, style, model_name)
                if inspect.isawaitable(r):
                    await r
            await asyncio.sleep(self.delay)
            if "REFUSE" in body:
                raise ModelRefused(body)
            if "BOOM" in body:
                raise ModelError(body)
            return f"[{style}|{model_name}] {body}"
        finally:
            self.active -= 1
