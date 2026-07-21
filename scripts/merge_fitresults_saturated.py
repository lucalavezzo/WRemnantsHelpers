#!/usr/bin/env python3
"""Graft the saturated-test scalars from one fitresults.hdf5 into another.

Why: the split fitterSCETlibNP.py workflow computes the postfit hists WITH
errors in the hessian step (cov/fitresults.hdf5, straight-through mode) and
the ptll-projection saturated test in the exact-mode saturated step
(saturated/fitresults.hdf5, --noHessian, no hist errors). rabbit_plot_hists.py
reads BOTH the hists and the chi2 from the single file it plots, so neither
output alone can make the banded postfit plot with the saturated p-value.
Rather than re-running the saturated refit inside the straight-through cov
pass (correct but painfully slow: ~9 bT-fold passes per refit iteration),
this merges the two outputs: it copies the destination file and inserts the
``*_saturated`` scalars (chi2_saturated, ndf_saturated, edmval_saturated)
from the source file's mapping results.

Usage (inside the container, wums/h5py needed)::

    merge_fitresults_saturated.py <dest=cov/fitresults.hdf5> \\
        <src=saturated/fitresults.hdf5> -o merged/fitresults.hdf5

then plot from the merged file, e.g.::

    rabbit_plot_hists.py merged/fitresults.hdf5 -m 'Project ch0 ptll' ...

Both inputs must come from the SAME postfit point (the fitterSCETlibNP.py
hessian and saturated steps both --externalPostfit the same fit result); this
is asserted by comparing the stored parameter values.

Provenance: the merged file's meta gains a ``merged_saturated_from`` entry
recording the source path and its meta_info command.
"""

import argparse
import os
import sys

import h5py
import numpy as np

from wums import ioutils

SATURATED_SUFFIX = "_saturated"


def load_results_groups(f):
    """{group_name: unpickled results dict} for every results* group."""
    return {
        k: ioutils.pickle_load_h5py(f[k]) for k in f.keys() if k.startswith("results")
    }


def materialize(obj):
    """Recursively force-load every H5PickleProxy so a later re-dump writes
    the real objects (wums dumps proxy.obj, which is None while lazy)."""
    if isinstance(obj, ioutils.H5PickleProxy):
        obj.get()
        return
    if isinstance(obj, dict):
        for v in obj.values():
            materialize(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            materialize(v)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("dest", help="fitresults with the hists+errors (cov pass output)")
    p.add_argument(
        "src", help="fitresults with the saturated test (saturated step output)"
    )
    p.add_argument(
        "-o", "--output", required=True, help="merged output file (must not exist)"
    )
    args = p.parse_args()

    if os.path.exists(args.output):
        sys.exit(f"{args.output} exists; refusing to overwrite.")
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    with h5py.File(args.dest, "r") as fdest, h5py.File(args.src, "r") as fsrc:
        dest_results = load_results_groups(fdest)
        src_results = load_results_groups(fsrc)
        if not dest_results:
            sys.exit(f"{args.dest}: no results* group (aborted-fit stub?)")
        if not src_results:
            sys.exit(f"{args.src}: no results* group (aborted-fit stub?)")

        # same-postfit guard: both steps ran --externalPostfit on the same fit.
        # --externalPostfit outputs have no top-level 'x', so compare the parms
        # hist stored in the results.
        def parms_values(groups):
            for res in groups.values():
                if "parms" in res:
                    p = res["parms"]
                    return np.asarray(
                        (
                            p.get() if isinstance(p, ioutils.H5PickleProxy) else p
                        ).values()
                    )
            return None

        pd_, ps_ = parms_values(dest_results), parms_values(src_results)
        if pd_ is not None and ps_ is not None:
            if pd_.shape != ps_.shape or not np.array_equal(pd_, ps_):
                sys.exit(
                    "dest and src postfit parameter values differ — these "
                    "fitresults are not from the same postfit point."
                )
        else:
            print(
                "WARNING: no parms found in one of the inputs; cannot verify "
                "they share the same postfit point."
            )

        meta = ioutils.pickle_load_h5py(fdest["meta"])
        src_meta = ioutils.pickle_load_h5py(fsrc["meta"])

        # graft: for each dest results group, take the matching src group
        # (same name, else the sole one) and copy the *_saturated scalars of
        # every common mapping
        n_copied = 0
        for gname, dres in dest_results.items():
            if gname in src_results:
                sres = src_results[gname]
            elif len(src_results) == 1:
                (sres,) = src_results.values()
            else:
                print(f"WARNING: no matching '{gname}' in src; skipping")
                continue
            dmaps = dres.get("mappings", {})
            for mkey, smap in sres.get("mappings", {}).items():
                sat_items = {
                    k: v for k, v in smap.items() if k.endswith(SATURATED_SUFFIX)
                }
                if not sat_items:
                    continue
                if mkey not in dmaps:
                    print(
                        f"WARNING: mapping '{mkey}' not in dest '{gname}' — the "
                        f"dest pass must save it too (-m {mkey}), else the "
                        "plotter has no hists for it; skipping"
                    )
                    continue
                for key, val in sat_items.items():
                    dmaps[mkey][key] = val
                    n_copied += 1
                    print(f"{gname} / {mkey}: {key} = {val}")
        if n_copied == 0:
            sys.exit(
                "nothing grafted: either the src has no *_saturated entries "
                "(run it with -m Project ... --computeSaturatedProjectionTests) "
                "or the dest lacks the matching mapping (run the cov pass with "
                "the same -m)."
            )

        meta["merged_saturated_from"] = {
            "file": os.path.abspath(args.src),
            "command": (src_meta.get("meta_info", {}) or {}).get("command", ""),
        }

        # lazy hist proxies must hold their objects before the re-dump
        for dres in dest_results.values():
            materialize(dres)

        with h5py.File(args.output, "w") as fout:
            # everything except the groups we rewrite (x, parms, cov, hists, ...)
            rewritten = set(dest_results) | {"meta"}
            for k in fdest.keys():
                if k not in rewritten:
                    fdest.copy(k, fout)
            ioutils.pickle_dump_h5py("meta", meta, fout)
            for gname, dres in dest_results.items():
                ioutils.pickle_dump_h5py(gname, dres, fout)

    print(f"\nWrote {args.output} ({n_copied} saturated entries grafted)")


if __name__ == "__main__":
    main()
