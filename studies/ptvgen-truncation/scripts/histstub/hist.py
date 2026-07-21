"""Minimal stub of `hist` so the SCETlib bt-grid `generate` path imports in the
v15 container (which lacks hist). hist.* is only used in bins-mode functions in
scetlib_run.binning, never in bt-grid generation, so no-op placeholders suffice."""


class _AxisNS:
    def Variable(self, *a, **k):
        raise NotImplementedError("hist stub: bins-mode only")

    def Regular(self, *a, **k):
        raise NotImplementedError("hist stub: bins-mode only")


axis = _AxisNS()


class storage:  # noqa
    class Double: ...


class Hist:  # noqa
    def __init__(self, *a, **k):
        raise NotImplementedError("hist stub: bins-mode only")
