#!/usr/bin/env python3
r"""Write a copy of a datacard whose response matrix acts on a COARSER gen grid.

The point is to make the gen-grid resolution a variable a REAL rabbit fit can
see, without a new SCETlib cache. Coarsening is a linear map M on the gen index,
and under it

    R_raw_c(b, G) = sum_{g in G} R_raw(b, g)      N_gen_c(G) = sum_{g in G} N_gen(g)
    sigma_reco(b) = sum_G [R_raw_c/N_gen_c](b, G) * sum_{g in G} sigma_gen(g)

which is the same as folding the ORIGINAL 210-column response with

    R_raw_eff(b, g) = N_gen(g) * R_raw_c(b, G(g)) / N_gen_c(G(g)) .

R_raw_eff has the shape the card already stores and divides by the same stored
N_gen, so the datacard, the cache, the parameter set and the fit configuration
are untouched: the ONLY thing that changes between arms is how finely the
response resolves the gen grid. That is what makes an A/B between them a
measurement of the grid rather than of two different builds.

Only ``auxiliary/scetlib_np/R`` is rewritten; ``N_gen`` and the edges are left
alone (the coarsening is folded into R, so the card still declares the gen
binning it was built with -- deliberately, because the model's cache is on that
binning).

Usage:
    ./coarsen_card_R.py --card <in.hdf5> --out <out.hdf5> --kqt 2 [--ky 1]
"""

import argparse
import os
import shutil

import h5py
import hdf5plugin  # noqa: F401  registers the Blosc2/LZ4 filter rabbit writes with
import numpy as np

GROUP = "auxiliary/scetlib_np"


def block_merge(n, k):
    """(n_coarse, n) 0/1 matrix merging consecutive blocks of k, last block
    taking the remainder."""
    rows = []
    i = 0
    while i < n:
        j = min(i + k, n)
        r = np.zeros(n)
        r[i:j] = 1.0
        rows.append(r)
        i = j
    return np.array(rows)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--card", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--kqt", type=int, default=1)
    ap.add_argument("--ky", type=int, default=1)
    ap.add_argument("--keep-tail", type=int, default=1,
                    help="trailing gen qT bins left unmerged (the ptVGen "
                         "overflow: a RANGE artefact, not granularity)")
    args = ap.parse_args()

    if os.path.abspath(args.card) == os.path.abspath(args.out):
        raise SystemExit("refusing to overwrite the input card")
    shutil.copyfile(args.card, args.out)

    with h5py.File(args.out, "r+") as f:
        g = f[GROUP]
        Te = np.asarray(g["edges__ptVGen"], float)
        Ye = np.asarray(g["edges__absYVGen"], float)
        nT, nY = Te.size - 1, Ye.size - 1
        N = np.asarray(g["N_gen"], float).reshape(-1)
        R = np.asarray(g["R"], float)
        n_reco = R.size // (nT * nY)
        R = R.reshape(n_reco, nT * nY)

        head = nT - args.keep_tail
        MQ = np.zeros((0, nT))
        if args.kqt > 1:
            MQ = np.zeros((0, nT))
            blocks = block_merge(head, args.kqt)
            MQ = np.zeros((blocks.shape[0] + args.keep_tail, nT))
            MQ[: blocks.shape[0], :head] = blocks
            for t in range(args.keep_tail):
                MQ[blocks.shape[0] + t, head + t] = 1.0
        else:
            MQ = np.eye(nT)
        MY = block_merge(nY, args.ky) if args.ky > 1 else np.eye(nY)
        M = np.kron(MQ, MY)                       # gen flattened qT-major

        Nc = M @ N
        Rc = R @ M.T
        safe = np.where(Nc > 0, Nc, 1.0)
        Pc = Rc / safe[np.newaxis, :]             # (n_reco, n_coarse)
        # expand back onto the original 210 columns, multiplied by N_gen
        R_eff = (Pc @ M) * N[np.newaxis, :]

        # sanity: the reco marginal must be untouched by construction wherever
        # N_gen > 0 (each coarse group redistributes its own events).
        a = (R @ np.ones(nT * nY))
        b = (R_eff @ np.ones(nT * nY))
        print(f"gen grid {nT} x {nY} -> {MQ.shape[0]} x {MY.shape[0]} "
              f"= {MQ.shape[0] * MY.shape[0]} effective bins")
        print(f"reco marginal sum R vs R_eff: max rel diff "
              f"{np.max(np.abs(b / np.where(a > 0, a, 1) - 1)):.2e}")
        print(f"R total {R.sum():.8g} -> {R_eff.sum():.8g}")
        g["R"][...] = R_eff.reshape(-1)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
