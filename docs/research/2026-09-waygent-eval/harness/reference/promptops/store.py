from dataclasses import dataclass, field, replace
import itertools

_GEN = itertools.count(1)

from .errors import PromptOpsError
from .events import EventLog


class PromptMissing(PromptOpsError, KeyError):
    pass


class VersionConflict(PromptOpsError):
    def __init__(self, current_version):
        super().__init__(current_version)
        self.current_version = current_version


@dataclass
class Prompt:
    id: str
    body: str
    version: int = 1
    generation: int = field(default=0, compare=False, repr=False)


class PromptStore:
    def __init__(self, events=None):
        self._items = {}
        self.events = events if events is not None else EventLog()

    def create(self, pid, body):
        if pid in self._items:
            raise ValueError(pid)
        self._items[pid] = Prompt(pid, body, 1, next(_GEN))
        self.events.emit("prompt.created", id=pid)
        return replace(self._items[pid])

    def get(self, pid):
        try:
            return replace(self._items[pid])
        except KeyError:
            raise PromptMissing(pid) from None

    def save(self, pid, body, expected_version, *, expected_generation=None):
        cur = self._items.get(pid)
        if cur is None:
            raise PromptMissing(pid)
        if cur.version != expected_version or (expected_generation is not None and cur.generation != expected_generation):
            raise VersionConflict(cur.version)
        self._items[pid] = Prompt(pid, body, cur.version + 1, cur.generation)
        self.events.emit("prompt.saved", id=pid, version=cur.version + 1)
        return replace(self._items[pid])

    def delete(self, pid):
        self.get(pid)
        del self._items[pid]
        self.events.emit("prompt.deleted", id=pid)

    def list_ids(self):
        return sorted(self._items)
