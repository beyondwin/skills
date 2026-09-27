from dataclasses import dataclass, replace


class PromptMissing(KeyError):
    pass


class VersionConflict(Exception):
    def __init__(self, current_version):
        super().__init__(current_version)
        self.current_version = current_version


@dataclass
class Prompt:
    id: str
    body: str
    version: int = 1


class PromptStore:
    def __init__(self):
        self._items = {}

    def create(self, pid, body):
        if pid in self._items:
            raise ValueError(pid)
        self._items[pid] = Prompt(pid, body, 1)
        return replace(self._items[pid])

    def get(self, pid):
        try:
            return replace(self._items[pid])
        except KeyError:
            raise PromptMissing(pid) from None

    def save(self, pid, body, expected_version):
        cur = self._items.get(pid)
        if cur is None:
            raise PromptMissing(pid)
        if cur.version != expected_version:
            raise VersionConflict(cur.version)
        self._items[pid] = Prompt(pid, body, cur.version + 1)
        return replace(self._items[pid])

    def delete(self, pid):
        self.get(pid)
        del self._items[pid]

    def list_ids(self):
        return sorted(self._items)
