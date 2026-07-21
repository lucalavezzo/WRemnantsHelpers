#!/usr/bin/env python3
"""Independently diff two rabbit datacards and prove only the intended process
changed. Re-reads both files from scratch (does not trust the editor).

Checks:
  1. hnorm / hsumw / hsumw2 / hdata_obs / hconstraintweights / hsysts / hprocs
     are byte-identical.
  2. hlogk: per process, count how many (bin, proc) rows differ and the max
     |diff|. Non-target processes MUST be identical (0 rows, 0 diff).
  3. For the target process, the changed rows must all be exactly zero in the
     new card (a zeroing, not some other change).

Usage: verify_cards_diff.py ORIG.hdf5 NEW.hdf5 [--process Ztautau]
"""

import argparse

import hdf5plugin  # noqa: F401
import h5py
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("orig")
    p.add_argument("new")
    p.add_argument("--process", nargs="+", default=["Ztautau"])
    args = p.parse_args()

    fa = h5py.File(args.orig, "r")
    fb = h5py.File(args.new, "r")
    procs = [x.decode() if isinstance(x, bytes) else x for x in fa["hprocs"][:]]
    NPROC = len(procs)
    NS = int(fa["hlogk"].attrs["original_shape"][2])
    nb = int(fa["hnorm"].attrs["original_shape"][0])

    print("=== 1. non-logk datasets must be byte-identical ===")
    ok_all = True
    for k in ["hnorm", "hsumw", "hsumw2", "hdata_obs", "hconstraintweights"]:
        a = fa[k][:]
        b = fb[k][:]
        same = a.shape == b.shape and np.array_equal(a, b)
        ok_all &= same
        print(f"  {k:20s}: {'IDENTICAL' if same else 'DIFFERS !!!'}")
    for k in ["hprocs", "hsysts"]:
        same = list(fa[k][:]) == list(fb[k][:])
        ok_all &= same
        print(f"  {k:20s}: {'IDENTICAL' if same else 'DIFFERS !!!'}")

    print("\n=== 2. hlogk diff per process ===")
    dsa = fa["hlogk"]
    dsb = fb["hlogk"]
    changed = np.zeros(NPROC, dtype=np.int64)
    maxdiff = np.zeros(NPROC)
    tgt = [procs.index(pr) for pr in args.process]
    nonzero_after = np.zeros(NPROC, dtype=np.int64)  # target rows not fully zeroed
    rp = (40_000_000 // NS) * NPROC
    for r0 in range(0, nb * NPROC, rp):
        r1 = min(r0 + rp, nb * NPROC)
        A = dsa[r0 * NS : r1 * NS].reshape((r1 - r0) // NPROC, NPROC, NS)
        B = dsb[r0 * NS : r1 * NS].reshape((r1 - r0) // NPROC, NPROC, NS)
        d = np.abs(A - B)
        row_changed = d.max(axis=2) > 0  # (chunk_bins, nproc)
        changed += row_changed.sum(axis=0)
        maxdiff = np.maximum(
            maxdiff,
            d.max(axis=(0, 1)) if False else d.reshape(-1, NPROC, NS).max(axis=(0, 2)),
        )
        for ip in tgt:
            # among changed rows of the target, is the NEW value all zero?
            ch = row_changed[:, ip]
            if ch.any():
                nonzero_after[ip] += int((np.abs(B[ch, ip, :]).max(axis=1) > 0).sum())
    for ip, pr in enumerate(procs):
        tag = "(target)" if ip in tgt else "(should be UNTOUCHED)"
        flag = "" if (ip in tgt or changed[ip] == 0) else "   <<< UNEXPECTED CHANGE"
        print(
            f"  {pr:14s} {tag:22s}: {changed[ip]:6d} rows changed, "
            f"max|diff|={maxdiff[ip]:.3g}{flag}"
        )
        if ip not in tgt and changed[ip] != 0:
            ok_all = False

    print("\n=== 3. target changed rows are all zero in the new card ===")
    for ip in tgt:
        good = nonzero_after[ip] == 0
        ok_all &= good
        print(
            f"  {procs[ip]:14s}: {changed[ip]} changed rows, "
            f"{nonzero_after[ip]} still non-zero -> "
            f"{'ALL ZEROED' if good else 'NOT all zero !!!'}"
        )

    fa.close()
    fb.close()
    print(
        "\n"
        + (
            "PASS: only the target process changed, and only by zeroing."
            if ok_all
            else "FAIL: see flags above."
        )
    )
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
