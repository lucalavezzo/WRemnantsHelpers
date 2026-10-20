#!/usr/bin/env python3
"""Compare two rabbit fitresults files.

  compare_fitresults.py A.hdf5 B.hdf5 [--rtol 0] [--atol 0] [--ignore REGEX ...]

Walks every result (hists -> values/variances, scalars, arrays) with
rabbit.io_tools.get_fitresult and reports the largest difference per key.
Exit 0 iff everything agrees within the tolerances (default: bit-identical).
Metadata (meta_info: command lines, git hashes, timestamps) is skipped.
"""

import argparse
import re
import sys

import numpy as np

from rabbit import io_tools


def leaves(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{prefix}/{k}")
        return
    if hasattr(obj, "get") and callable(obj.get) and not isinstance(obj, dict):
        try:
            obj = obj.get()
        except Exception:
            pass
    if hasattr(obj, "values") and hasattr(obj, "axes"):
        yield f"{prefix}:values", np.asarray(obj.values(flow=True), dtype=np.float64)
        var = obj.variances(flow=True)
        if var is not None:
            yield f"{prefix}:variances", np.asarray(var, dtype=np.float64)
        return
    if isinstance(obj, (list, tuple)):
        try:
            arr = np.asarray(obj, dtype=np.float64)
            yield prefix, arr
        except (TypeError, ValueError):
            yield prefix, str(obj)
        return
    if isinstance(obj, (int, float, np.integer, np.floating, bool, np.bool_)):
        yield prefix, np.asarray(float(obj))
        return
    if isinstance(obj, np.ndarray):
        if obj.dtype.kind in "fiub":
            yield prefix, obj.astype(np.float64)
        else:
            yield prefix, str(obj.tolist())
        return
    yield prefix, str(obj)


def load(fn):
    """Every results group in the file (data fit, asimov, each toy)."""
    import h5py

    out = {}
    with h5py.File(fn, "r") as f:
        keys = [k for k in f.keys() if k.startswith("results")]
        for k in keys:
            suffix = None if k == "results" else k[len("results_") :]
            out.update(leaves(io_tools.get_fitresult(f, result=suffix), prefix=k))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--rtol", type=float, default=0.0)
    ap.add_argument("--atol", type=float, default=0.0)
    ap.add_argument("--ignore", nargs="*", default=["meta", "time", "epoch"])
    args = ap.parse_args()
    ra, rb = load(args.a), load(args.b)
    ign = [re.compile(p) for p in args.ignore]
    keys = sorted(k for k in set(ra) | set(rb) if not any(p.search(k) for p in ign))
    bad, n, worst = [], 0, 0.0
    for k in keys:
        if k not in ra or k not in rb:
            bad.append(f"MISSING {k} (in {'A' if k in ra else 'B'} only)")
            continue
        x, y = ra[k], rb[k]
        n += 1
        if isinstance(x, str) or isinstance(y, str):
            if str(x) != str(y):
                bad.append(f"DIFF {k}: {str(x)[:80]} != {str(y)[:80]}")
            continue
        if x.shape != y.shape:
            bad.append(f"SHAPE {k}: {x.shape} != {y.shape}")
            continue
        same_nan = np.isnan(x) == np.isnan(y)
        with np.errstate(invalid="ignore"):
            d = np.where((x == y) | (np.isnan(x) & np.isnan(y)), 0.0, np.abs(x - y))
        tol = args.atol + args.rtol * np.abs(y)
        dmax = float(np.nanmax(d)) if d.size else 0.0
        worst = max(worst, dmax)
        if not same_nan.all() or np.any(d > tol):
            bad.append(f"DIFF {k}: max |diff| {dmax:.3g}")
    print(f"compared {n} leaves; worst |diff| {worst:.3g}; {len(bad)} mismatching")
    for b in bad[:40]:
        print("  ", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
