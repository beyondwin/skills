"""Domain error base. Every promptops exception derives from PromptOpsError so the UI can
catch one type and show a readable message; plain KeyError/ValueError never reach the UI."""


class PromptOpsError(Exception):
    """Base for all promptops domain errors."""
