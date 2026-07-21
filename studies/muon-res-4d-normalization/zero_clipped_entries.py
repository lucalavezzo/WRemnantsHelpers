#!/usr/bin/env python3
"""Build a datacard that ZEROES exactly the logk entries that a clipped card
modified, leaving everything else identical to the unclipped card.

Purpose: disentangle the two knobs that make clipping != per-bin-zeroing.
Clipping and zeroing differ in (A) ACTION on a modified entry (clip caps it at
±log(x); zero sets it to 0) and (B) FOOTPRINT (which entries are modified). To
isolate (A), we match clip's footprint EXACTLY and change only the action:
take the unclipped card and set to 0 precisely the entries where the clipped
card differs from it. clip-vs-this then differs ONLY in bounded-10x vs 0 on an
identical set of entries.

The clipped card MUST be a pure logk-clip of the unclipped card (same nominal /
sumw2 / data / systs / procs) — checked here.

Runs on the login node (h5py only). The unclipped card is never modified; a new
file is written (copy-then-patch).

Usage:
  zero_clipped_entries.py UNCLIPPED.hdf5 CLIPPED.hdf5 -o OUT.hdf5
"""

import argparse
import os
import shutil

import hdf5plugin  # noqa: F401
import h5py
import numpy as np


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("unclipped")
    p.add_argument("clipped")
    p.add_argument("-o", "--output", required=True)
    args = p.parse_args()

    with h5py.File(args.unclipped, "r") as fu, h5py.File(args.clipped, "r") as fc:
        NPROC = len(fu["hprocs"][:])
        NS = int(fu["hlogk"].attrs["original_shape"][2])
        nb = int(fu["hnorm"].attrs["original_shape"][0])
        procs = [x.decode() if isinstance(x, bytes) else x for x in fu["hprocs"][:]]
        # sanity: pure logk-clip
        for k in ["hnorm", "hsumw2", "hdata_obs"]:
            if not np.array_equal(fu[k][:], fc[k][:]):
                raise SystemExit(
                    f"{k} differs between unclipped and clipped -> "
                    "not a pure logk-clip; aborting."
                )
        if list(fu["hsysts"][:]) != list(fc["hsysts"][:]):
            raise SystemExit("hsysts differ; aborting.")

    if os.path.abspath(args.output) == os.path.abspath(args.unclipped):
        raise SystemExit("output must differ from the unclipped input")
    print(f"# copying unclipped -> {args.output}")
    shutil.copy2(args.unclipped, args.output)

    # stream: where clipped != unclipped, set output(=unclipped copy) to 0
    per_proc_zeroed = np.zeros(NPROC, dtype=np.int64)
    max_abs_zeroed = 0.0
    with h5py.File(args.output, "r+") as fo, h5py.File(args.clipped, "r") as fc:
        dso = fo["hlogk"]
        dsc = fc["hlogk"]
        nrow = nb * NPROC
        rows_per_chunk = max(1, 40_000_000 // NS)
        for r0 in range(0, nrow, rows_per_chunk):
            r1 = min(r0 + rows_per_chunk, nrow)
            u = dso[r0 * NS : r1 * NS].reshape(r1 - r0, NS)
            c = dsc[r0 * NS : r1 * NS].reshape(r1 - r0, NS)
            mask = u != c  # entries clip modified
            if mask.any():
                max_abs_zeroed = max(max_abs_zeroed, np.abs(u[mask]).max())
                # per-process tally
                procidx = np.arange(r0, r1) % NPROC
                per_proc_zeroed += np.array(
                    [mask[procidx == ip].sum() for ip in range(NPROC)]
                )
                u[mask] = 0.0
                dso[r0 * NS : r1 * NS] = u.reshape(-1)
    tot = int(per_proc_zeroed.sum())
    print(f"# zeroed {tot} logk entries (exactly the clip footprint)")
    for ip, pr in enumerate(procs):
        print(f"#   {pr:14s}: {int(per_proc_zeroed[ip]):>9d} entries")
    print(
        f"# max |logk| among zeroed entries (unclipped value) = {max_abs_zeroed:.3f} "
        f"(ratio {np.exp(max_abs_zeroed):.3g}x) -> confirms these are the big ones"
    )


if __name__ == "__main__":
    main()
