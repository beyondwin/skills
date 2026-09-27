"""Append-only event log. The UI and the audit export subscribe to it.

Convention: emit after the change is committed, once per change, never for a change that
did not happen. Payloads are plain dicts of str/int values.
"""


class EventLog:
    def __init__(self):
        self.items: list[tuple[str, dict]] = []

    def emit(self, kind: str, **data) -> None:
        self.items.append((kind, dict(data)))

    def of(self, kind: str) -> list[dict]:
        return [d for k, d in self.items if k == kind]
