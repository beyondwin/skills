from .store import PromptMissing


class EditSession:
    def __init__(self, store, pid):
        self.store, self.pid = store, pid
        p = store.get(pid)
        self.body, self.base_version, self.gen = p.body, p.version, p.generation
        self.dirty = self.conflict = self.missing = False

    def edit(self, body):
        self.body, self.dirty = body, True

    def save(self):
        if self.missing:
            raise PromptMissing(self.pid)
        p = self.store.save(self.pid, self.body, self.base_version, expected_generation=self.gen)
        self.base_version, self.dirty, self.conflict = p.version, False, False
        return p

    def reload(self):
        try:
            p = self.store.get(self.pid)
        except PromptMissing:
            self.missing = True
            return
        self.missing = False
        if p.version == self.base_version and p.generation == self.gen:
            return
        if self.dirty:
            self.conflict = True
        else:
            self.body, self.base_version, self.gen = p.body, p.version, p.generation

    def discard(self):
        p = self.store.get(self.pid)
        self.body, self.base_version, self.gen = p.body, p.version, p.generation
        self.dirty = self.conflict = False
