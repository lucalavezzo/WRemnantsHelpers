"""List the structure of a rabbit fitresult (keys, hist axes). Prints NO parameter values."""

import sys
from rabbit import io_tools

fr, meta = io_tools.get_fitresult(sys.argv[1], meta=True)


def walk(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict):
            print(pre + k + "/")
            walk(v, pre + "  ")
        else:
            h = v.get() if hasattr(v, "get") else v
            ax = getattr(h, "axes", None)
            desc = (
                [(a.name, len(a)) for a in ax] if ax is not None else type(h).__name__
            )
            print(pre + k, desc)


walk(fr)
