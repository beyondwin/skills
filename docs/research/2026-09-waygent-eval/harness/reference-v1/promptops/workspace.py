from .batch import BatchRun


class Busy(Exception):
    pass


class Workspace:
    def __init__(self, store, model):
        self.store, self.model = store, model
        self.selected_model, self.selected_style = "base", "plain"
        self._run = None

    @property
    def busy(self):
        return self._run is not None

    async def run_batch(self, pids, limit=3):
        if self._run is not None:
            raise Busy()
        self._run = BatchRun(self.store, self.model, pids, style=self.selected_style,
                             model_name=self.selected_model, limit=limit)
        try:
            return await self._run.run()
        finally:
            self._run = None

    def cancel(self):
        if self._run is not None:
            self._run.cancel()
