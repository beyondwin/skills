"""In-memory prompt store."""
from dataclasses import dataclass

from .errors import PromptOpsError
from .events import EventLog


class PromptMissing(PromptOpsError, KeyError):
    """The prompt id does not exist (never created, or deleted)."""


@dataclass
class Prompt:
    id: str
    body: str


class PromptStore:
    def __init__(self, events: EventLog | None = None):
        self._items: dict[str, Prompt] = {}
        self.events = events if events is not None else EventLog()

    def create(self, pid: str, body: str) -> Prompt:
        if pid in self._items:
            raise ValueError(f"prompt {pid!r} already exists")
        self._items[pid] = Prompt(pid, body)
        self.events.emit("prompt.created", id=pid)
        return self._items[pid]

    def get(self, pid: str) -> Prompt:
        try:
            return self._items[pid]
        except KeyError:
            raise PromptMissing(pid) from None

    def put(self, pid: str, body: str) -> Prompt:
        """Last write wins."""
        p = self.get(pid)
        p.body = body
        self.events.emit("prompt.saved", id=pid)
        return p

    def delete(self, pid: str) -> None:
        self.get(pid)
        del self._items[pid]
        self.events.emit("prompt.deleted", id=pid)

    def list_ids(self) -> list[str]:
        return sorted(self._items)
