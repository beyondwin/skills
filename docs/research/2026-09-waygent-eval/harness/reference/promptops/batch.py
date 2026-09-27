import asyncio

from .concurrency import gather_limited
from .fake_model import ModelRefused
from .modelcall import restyle
from .store import PromptMissing, VersionConflict


class BatchRun:
    def __init__(self, store, model, pids, *, style, model_name, limit=3):
        self.store, self.model, self.pids = store, model, list(pids)
        self.style, self.model_name, self.limit = style, model_name, limit
        self.outcomes, self.state = {}, "idle"
        self._cancelled, self._task, self._before, self._undone = False, None, {}, False

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
            if self._cancelled:
                raise asyncio.CancelledError
            body = await restyle(self.model, p.body, self.style, self.model_name)
            if self._cancelled:
                raise asyncio.CancelledError
            saved = self.store.save(pid, body, p.version)
            self._before[pid] = (p.body, saved.version)
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
        self.store.events.emit("batch.progress", **self.counts)

    async def run(self):
        try:
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
        finally:
            self.state = "cancelled" if self._cancelled else "done"
            self.store.events.emit("batch.finished", state=self.state, **self.counts)
        return dict(self.outcomes)

    def cancel(self):
        if self.state == "done":
            return
        self._cancelled = True
        if self._task is not None:
            self._task.cancel()

    def undo(self):
        if self.state not in ("done", "cancelled") or self._undone:
            raise RuntimeError("cannot undo")
        self._undone = True
        out = {}
        for pid, (body, ver) in self._before.items():
            try:
                self.store.save(pid, body, ver)
                out[pid] = "restored"
            except VersionConflict:
                out[pid] = "skipped:changed"
            except PromptMissing:
                out[pid] = "skipped:missing"
        return out
