import sys
from rabbit import io_tools

fr = sys.argv[1]
res, meta = io_tools.get_fitresult(fr, meta=True)


def walk(d, pre="", depth=0):
    if depth > 4:
        return
    try:
        keys = list(d.keys())
    except Exception:
        return
    for k in keys:
        v = d[k]
        if hasattr(v, "keys"):
            print("  " * depth + f"[dict] {pre}{k}")
            walk(v, pre + k + "/", depth + 1)
        else:
            try:
                h = v.get()
                print(
                    "  " * depth + f"[hist] {pre}{k} axes="
                    f"{[(a.name, len(a)) for a in h.axes]}"
                )
            except Exception:
                print("  " * depth + f"[val ] {pre}{k} = {v!r}"[:160])


walk(res)
