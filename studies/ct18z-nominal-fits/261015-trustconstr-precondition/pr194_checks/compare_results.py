"""Compare rabbit fitresults from WMass/rabbit main vs PR #194, leaf by leaf.

Walks the whole pickled `results` group (and `meta` is skipped: it holds timestamps and the command). Every hist is
compared by values and variances, every array/scalar exactly (bit-identity = max |diff| == 0), dicts recursively.
Keys present on one side only are listed (the PR adds `optimality_frame` to a trust-constr minimizer_status).
usage: python compare_results.py <a.hdf5> <b.hdf5>
"""

import sys

import h5py
import numpy as np
from wums import ioutils


def load(path):
    with h5py.File(path, "r") as f:
        return materialize(ioutils.pickle_load_h5py(f["results"]))


def materialize(o):
    if hasattr(o, "get") and not isinstance(o, dict):
        try:
            o = o.get()
        except Exception:
            pass
    if isinstance(o, dict):
        return {k: materialize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [materialize(v) for v in o]
    return o


def leaves(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, f"{path}[{i}]")
    elif hasattr(o, "values") and hasattr(o, "axes"):
        yield f"{path}.values", np.asarray(o.values(flow=True), dtype=float)
        var = o.variances(flow=True)
        if var is not None:
            yield f"{path}.variances", np.asarray(var, dtype=float)
    else:
        yield path, o


def main(a, b):
    la, lb = dict(leaves(load(a))), dict(leaves(load(b)))
    only_a, only_b = sorted(set(la) - set(lb)), sorted(set(lb) - set(la))
    worst, nonident, n = 0.0, [], 0
    skipped = [k for k in set(la) & set(lb) if "time" in k.lower()]
    for k in sorted(set(la) & set(lb) - set(skipped)):
        x, y = la[k], lb[k]
        n += 1
        try:
            xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
            if xa.shape != ya.shape:
                nonident.append((k, "shape", np.nan))
                continue
            same = (xa == ya) | (np.isnan(xa) & np.isnan(ya))  # also equal infinities
            with np.errstate(invalid="ignore"):
                d = np.where(same, 0.0, np.abs(xa - ya))
            m = float(np.nanmax(d)) if d.size else 0.0
            if m != 0.0 or np.any(np.isnan(d)):
                scale = (
                    float(np.nanmax(np.abs(np.where(same, 0.0, xa))))
                    if xa.size
                    else 0.0
                )
                nonident.append((k, m, m / scale if scale else np.inf))
                worst = max(worst, m)
        except (TypeError, ValueError):
            if x != y:
                nonident.append((k, f"{x!r} != {y!r}"[:120], np.nan))
    print(f"skipped (wall-clock): {sorted(skipped)}")
    print(f"compared {n} leaves; only in A: {only_a}; only in B: {only_b}")
    print(f"non-identical leaves: {len(nonident)}; worst |diff| {worst:.3e}")
    rels = [r for _, _, r in nonident if isinstance(r, float) and np.isfinite(r)]
    if rels:
        print(f"worst relative diff {max(rels):.3e}")
    for k, m, r in sorted(
        nonident,
        key=lambda t: -(t[2] if isinstance(t[2], float) and np.isfinite(t[2]) else 0),
    )[:12]:
        print(
            f"   {k}: abs {m}  rel {r:.2e}" if isinstance(r, float) else f"   {k}: {m}"
        )
    return 0 if not nonident else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
