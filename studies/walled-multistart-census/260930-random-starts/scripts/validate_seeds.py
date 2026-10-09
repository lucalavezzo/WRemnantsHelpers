#!/usr/bin/env python3
"""Independent checks of the seeds written by make_random_starts.py (no cache load).

    validate_seeds.py --ref <fitresults.hdf5> --dir <seed dir> --manifest <csv> [--s 2]

For every seed file in the manifest:
  1. LOAD through rabbit's real ``Fitter.load_fitresult`` (called unbound on a stand-in
     that carries only ``x``/``parms``/``cov``; profile=False so no bbstat is needed).
     The loaded x must equal the file's x bit-exactly, and the file's parms axis must be
     the reference's, same names, same order.
  2. RECONSTRUCT the intended vector from the reference + the manifest:
       perturb: alphaS == x_ref + u*sigma_ref bit-exactly; NP theta reproduces the
                manifest's physical lambdas; the non-NP displacement whitened with the
                same Cholesky factor, w = L^-1 (x - x_ref)/s, gives max|w| == manifest
                max|z| and w.w == chi2_z (i.e. it IS s*L*z for a standard-normal z).
       cold   : every non-alphaS entry == parms_prefit bit-exactly; alphaS == x_ref + u*sigma.
  3. FEASIBILITY: physical lambdas re-derived from the file's theta with the wall's own
     physical_from_theta, every armed condition >= bound at margin 0 and every held-only
     condition >= 0 (bare), with the wall's Condition objects + numpy_relu2.
Plus, once per reference: the reference's ``parms`` equals its converged
``snapshot_fitresults_*.hdf5`` x bit-exactly when that snapshot exists (so the stored
parms ARE the raw Fitter.x frame that --externalPostfit loads).

Prints no alphaS value, only pass/fail and u.
"""

import argparse
import csv
import os
import sys
import types

import h5py
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_random_starts as M  # noqa: E402


def load_via_rabbit(path, names):
    import tensorflow as tf
    from rabbit import fitter as rfitter

    stub = types.SimpleNamespace(
        x=tf.Variable(np.zeros(len(names), dtype=np.float64)),
        parms=np.array(names).astype(str),
        cov=None,
    )
    rfitter.Fitter.load_fitresult(stub, path, None, profile=False)
    return stub.x.numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--s", type=float, default=2.0)
    ap.add_argument("--poi", default="alphaS")
    ap.add_argument("--snapshot", default=None, help="default: sibling snapshot_<ref>")
    args = ap.parse_args()

    ref = M.load_reference(args.ref, poi=args.poi)
    names, x_ref, x0, cov = ref["names"], ref["x_ref"], ref["x0"], ref["cov"]
    wi = M.wall_inputs(ref)
    sampler = M.NPSampler(wi, names, M.DEFAULT_RANGES, 0.0)
    W = sampler.W
    ia = int(np.where(names == args.poi)[0][0])
    sig_a = float(np.sqrt(cov[ia, ia]))
    mask_non = np.ones(len(names), dtype=bool)
    for n in sampler.fitted:
        mask_non[sampler.idx[n]] = False
    mask_non[ia] = False
    idx_non = np.where(mask_non)[0]
    L = None

    allok = True

    snap = args.snapshot or os.path.join(
        os.path.dirname(args.ref), "snapshot_" + os.path.basename(args.ref)
    )
    if os.path.exists(snap):
        with h5py.File(snap, "r") as f:
            xs = f["x"][...]
            ns = f["parms"][...].astype(str)
            reason = f.attrs.get("reason")
        same = np.array_equal(ns, names) and np.array_equal(
            xs.view(np.uint64), x_ref.view(np.uint64)
        )
        print(
            f"[frame] reference parms == converged snapshot x bit-exactly: {same} "
            f"(snapshot reason={reason!r})"
        )
    else:
        print(f"[frame] no snapshot at {snap}; frame check skipped")

    rows = list(csv.DictReader(open(args.manifest)))
    for r in rows:
        path = os.path.join(args.dir, r["file"])
        with h5py.File(path, "r") as f:
            xf = f["x"][...]
            nf = f["parms"][...].astype(str)
            keys = sorted(f.keys())
        xl = load_via_rabbit(path, names)
        c_names = np.array_equal(nf, names)
        c_load = np.array_equal(xl.view(np.uint64), xf.view(np.uint64))
        c_keys = keys == ["parms", "x"]
        u = float(r["u"])
        c_a = xf[ia] == x_ref[ia] + u * sig_a  # bit-exact float equality
        if r["mode"] == "perturb":
            if L is None:
                L = np.linalg.cholesky(cov[np.ix_(idx_non, idx_non)])
            import scipy.linalg as sl

            w = sl.solve_triangular(
                L, (xf[idx_non] - x_ref[idx_non]) / args.s, lower=True
            )
            c_z = abs(np.max(np.abs(w)) - float(r["max_abs_z"])) < 1e-8 and abs(
                w @ w - float(r["chi2_z"])
            ) < 1e-6 * len(w)
            zinfo = f"max|w|={np.max(np.abs(w)):.4f} (manifest {float(r['max_abs_z']):.4f}) w.w/n={w @ w / len(w):.4f}"
            c_rest = c_z
        else:
            others = np.ones(len(names), dtype=bool)
            others[ia] = False
            c_rest = np.array_equal(
                xf[others].view(np.uint64), x0[others].view(np.uint64)
            )
            zinfo = "non-alphaS == parms_prefit"
        phys = {
            n: float(W.physical_from_theta(wi["specs"][n], xf[sampler.idx[n]]))
            for n in sampler.fitted
        }
        c_np = all(abs(phys[n] - float(r[n])) < 1e-12 for n in sampler.fitted)
        ev = sampler.evaluate(phys)
        c_feas = all(val >= b for _, val, b, _ in ev)
        worst = min((val - b, lab) for lab, val, b, act in ev if act)
        ok = all([c_names, c_load, c_keys, c_a, c_rest, c_np, c_feas])
        allok &= ok
        print(
            f"[{r['file']}] {'PASS' if ok else 'FAIL'}  names/order={c_names} "
            f"rabbit-load bitexact={c_load} keys={c_keys} alphaS(u={u:+.3f}) bitexact={c_a} "
            f"{zinfo} ok={c_rest} NP={c_np} feasible(margin 0)={c_feas} "
            f"closest armed face {worst[0]:+.4g} [{worst[1]}]"
        )
    print(f"[validate] {'ALL PASS' if allok else 'FAILURES'} ({len(rows)} seeds)")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
