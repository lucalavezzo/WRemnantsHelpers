#!/usr/bin/env python3
"""Zero the systematic variations (logk) of a process in its statistically
near-empty bins, producing a new rabbit datacard.

Motivation: in the 4D Z datacards, a process (Ztautau) has bins whose nominal is
a mixed-sign MC weight-cancellation residual (n_eff = sumw^2/sumw2 << 1). There
the log-normal syst ratio logk = log(syst/nom) is floating-point noise and blows
up (|logk| up to ~55 -> e^55 ~ 1e24), which rabbit_debug_inputdata flags and
which makes rabbit_plot_inputdata explode. See LOGBOOK.md.

Aimed fix: for the given process, in bins with n_eff < threshold, set logk = 0
for ALL systematics (the bin then contributes its nominal with no systematic
variation). NOTHING ELSE is touched:
  - the nominal (hnorm/hsumw), hsumw2, hdata_obs are left byte-identical;
  - only the target process's logk rows in the flagged bins change;
  - all other processes are untouched by construction (we index the process).

Implementation is copy-then-patch: the original card is copied verbatim (all
datasets, attrs, groups, compression preserved) and only the targeted hlogk
rows are overwritten with zeros in the copy. The original is never modified.

Runs on the login node (h5py only, no TensorFlow / container).

Usage:
    zero_lowstat_systs.py CARD.hdf5 -o CARD_zeroed.hdf5 \\
        [--process Ztautau ...] [--neff 1.0]
"""

import argparse
import os
import shutil

import hdf5plugin  # noqa: F401  (registers the blosc filter used by the cards)
import h5py
import numpy as np


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("card", help="input rabbit datacard hdf5 (never modified)")
    p.add_argument("-o", "--output", required=True, help="output card path")
    p.add_argument(
        "--process",
        nargs="+",
        default=["Ztautau"],
        help="process(es) to zero (default: Ztautau). Only these " "are touched.",
    )
    p.add_argument(
        "--neff",
        type=float,
        default=1.0,
        help="zero logk in bins with n_eff = sumw^2/sumw2 < this "
        "(default 1.0 = fewer than one effective event).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be zeroed; do not write output",
    )
    args = p.parse_args()

    # ---- read layout + per-(bin,proc) n_eff from the ORIGINAL (read-only) ----
    with h5py.File(args.card, "r") as f:
        procs = [x.decode() if isinstance(x, bytes) else x for x in f["hprocs"][:]]
        NPROC = len(procs)
        NS = int(f["hlogk"].attrs["original_shape"][2])
        nb = int(f["hnorm"].attrs["original_shape"][0])
        sumw = f["hsumw"][:].reshape(nb, NPROC)
        sumw2 = f["hsumw2"][:].reshape(nb, NPROC)
        symmetric = int(f["hlogk"].attrs["original_shape"].shape[0]) == 3

    if not symmetric:
        raise SystemExit(
            "hlogk is not the symmetric [nb,nproc,nsyst] layout; "
            "this tool only handles symmetric_tensor cards."
        )
    for pr in args.process:
        if pr not in procs:
            raise SystemExit(f"process {pr!r} not in card procs {procs}")

    # target (bin, proc) rows to zero
    targets = {}  # proc_index -> array of bin indices
    for pr in args.process:
        ip = procs.index(pr)
        w = sumw[:, ip]
        w2 = sumw2[:, ip]
        ok = (w > 0) & (w2 > 0)
        neff = np.full(nb, np.inf)
        neff[ok] = w[ok] ** 2 / w2[ok]
        bins = np.where(ok & (neff < args.neff))[0]
        targets[ip] = bins

    print(f"# card:   {args.card}")
    print(
        f"# rule:   zero logk where n_eff < {args.neff}, for process(es) "
        f"{args.process}"
    )
    total_bins = 0
    for ip, bins in targets.items():
        w = sumw[:, ip]
        tot = w[w > 0].sum()
        aff = w[bins].sum()
        print(
            f"#   {procs[ip]:14s}: {len(bins):5d} bins -> zeroed  "
            f"(yield {aff:.4g} / {tot:.1f} = {100*aff/tot:.3f}% of process; "
            f"{NS} systs each)"
        )
        total_bins += len(bins)
    print(f"# total (bin,proc) rows to zero: {total_bins}")
    for ip in range(NPROC):
        if ip not in targets:
            print(f"#   {procs[ip]:14s}: UNTOUCHED")

    if args.dry_run:
        print("# --dry-run: no output written")
        return

    # ---- copy-then-patch ----
    if os.path.abspath(args.output) == os.path.abspath(args.card):
        raise SystemExit("output must differ from input (original is never modified)")
    print(f"# copying -> {args.output}")
    shutil.copy2(args.card, args.output)

    with h5py.File(args.output, "r+") as f:
        ds = f["hlogk"]  # flat 1D, length nb*NPROC*NS
        zeros = np.zeros(NS, dtype=ds.dtype)
        nwritten = 0
        for ip, bins in targets.items():
            for B in bins:
                start = (int(B) * NPROC + ip) * NS
                ds[start : start + NS] = zeros
                nwritten += 1
    print(f"# done: zeroed {nwritten} (bin,proc) logk rows in {args.output}")


if __name__ == "__main__":
    main()
