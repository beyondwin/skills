import asyncio

from .concurrency import gather_limited
from .fake_model import ModelRefused
from .store import PromptMissing, VersionConflict


class BatchRun:
    def __init__(self, store, model, pids, *, style, model_name, limit=3):
        self.store, self.model, self.pids = store, model, list(pids)
        self.style, self.model_name, self.limit = style, model_name, limit
        self.outcomes, self.state = {}, "idle"
        self._cancelled, self._task = False, None

    @property
    def locked(self):
        return self.state == "running"

    @property
    def counts(self):
        c = {"applied": 0, "rejected": 0, "failed": 0, "cancelled": 0}
        for o in self.outcomes.values():
            c["failed" if o.startswith("failed") else o] += 1
        c["total"] = len(self.pids)
        return c

    async def _one(self, pid):
        try:
            p = self.store.get(pid)
            body = await self.model.restyle(p.body, self.style, self.model_name)
            if self._cancelled:
                raise asyncio.CancelledError
            self.store.save(pid, body, p.version)
            r = "applied"
        except asyncio.CancelledError:
            raise
        except ModelRefused:
            r = "rejected"
        except VersionConflict:
            r = "failed:conflict"
        except PromptMissing:
            r = "failed:missing"
        except Exception:
            r = "failed:error"
        self.outcomes[pid] = r

    async def run(self):
        if not self._cancelled:
            self.state = "running"
            self._task = asyncio.ensure_future(gather_limited(self.pids, self._one, self.limit))
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            finally:
                self._task = None
        for pid in self.pids:
            self.outcomes.setdefault(pid, "cancelled")
        self.state = "cancelled" if self._cancelled else "done"
        return dict(self.outcomes)

    def cancel(self):
        if self.state in ("done",):
            return
        self._cancelled = True
        if self._task is not None:
            self._task.cancel()
