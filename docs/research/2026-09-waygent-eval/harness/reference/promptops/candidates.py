from .concurrency import gather_limited
from .modelcall import restyle


class CandidateSet:
    def __init__(self, store, pid, base_version, candidates, errors):
        self.store, self.pid, self.base_version = store, pid, base_version
        self.candidates, self.errors, self._chosen = candidates, errors, False

    @property
    def all_failed(self):
        return not self.candidates

    def choose(self, style):
        if self._chosen:
            raise RuntimeError("already chosen")
        body = self.candidates[style]
        p = self.store.save(self.pid, body, self.base_version)
        self._chosen = True
        return p


async def generate_candidates(store, model, pid, styles, *, model_name, limit=3):
    p = store.get(pid)
    res = await gather_limited(styles, lambda st: restyle(model, p.body, st, model_name), limit)
    ok = {st: r for st, r in res if not isinstance(r, BaseException)}
    err = {st: repr(r) for st, r in res if isinstance(r, BaseException)}
    return CandidateSet(store, pid, p.version, ok, err)
