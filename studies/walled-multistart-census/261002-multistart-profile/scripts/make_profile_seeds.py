#!/usr/bin/env python3
"""T6 multi-start profile seeds: 4 alphaS points x 3 starts, all in NOMSTIFF's BLINDED x frame.

    make_profile_seeds.py [--master-seed 20261002] [--kick 2.0]

Points: k = -2, -1, +1, +2 (labels M2, M1, P1, P2); x[alphaS] = x_NOM[alphaS] + k*sigma_NOM, where
sigma_NOM = sqrt(cov_NOM[alphaS, alphaS]) (additive blinding => sigma in x == sigma in alphaS).
Starts per point:
  W (warm)      the NOMSTIFF vector, only alphaS moved.
  R (perturbed) the census generator (T3 make_random_starts.py, run UNMODIFIED as a subprocess:
                --s 0.5, NP lambdas uniform over its default physical boxes with wall rejection at
                margin 0, --alphas-u 0), master seed --master-seed, child j for point j; then alphaS
                overwritten with the point's value (not drawn).
  K (kicked)    the NOMSTIFF vector, alphaS at the point, plus x_i += kick * sign_i * sigma_post_i for
                every pdfEig* and resumTNP_* parameter (sigma_post = NOMSTIFF postfit sigma), signs
                random +-1 from SeedSequence([master, 1]).spawn(4)[j]. Signs recorded in the manifest.
Every seed is written with rabbit's own snapshot writer (via T3's write_seed, bit-exact round trip).
BLINDING: nothing absolute about alphaS is printed or saved besides the blinded x inside the seed files
(exactly what every fitresult already stores). Logs/manifests carry only k and Delta/sigma.
"""
import argparse
import csv
import os
import re
import subprocess
import sys

import h5py
import numpy as np

T3 = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/260930-random-starts/scripts"
sys.path.insert(0, T3)
import make_random_starts as G  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261002_multistart_profile/seeds"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POINTS = [
    ("M1", -1.0),
    ("P1", +1.0),
    ("M2", -2.0),
    ("P2", +2.0),
]  # j = 0..3 (generator child j)
KICK_RE = re.compile(r"(pdfEig\d+|resumTNP_.*)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, default=20261002)
    ap.add_argument("--kick", type=float, default=2.0)
    args = ap.parse_args()
    os.makedirs(f"{OUT}/raw", exist_ok=True)

    ref = G.load_reference(REF)
    names, x_ref, cov = ref["names"], ref["x_ref"], ref["cov"]
    ia = int(np.where(names == "alphaS")[0][0])
    sig = np.sqrt(np.diag(cov))
    sig_a = float(sig[ia])
    kick_idx = np.array(
        [i for i, n in enumerate(names) if KICK_RE.fullmatch(n)], dtype=int
    )
    print(f"[ref] {REF}: {len(names)} parms; alphaS blinded (only k reported)")
    print(f"[kick] {len(kick_idx)} params: {', '.join(names[kick_idx])}")
    print(
        f"[kick] postfit sigma range {sig[kick_idx].min():.3f} .. {sig[kick_idx].max():.3f}"
    )
    # precision matrix for a quadratic start-cost estimate 0.5 d^T C^-1 d (all 3719+1 params)
    Cinv = np.linalg.inv(cov)

    # --- R: the census generator, unmodified, alphaS u = 0 (then overwritten) ---
    gen = [
        "python3",
        f"{T3}/make_random_starts.py",
        "--ref",
        REF,
        "--n",
        str(len(POINTS)),
        "--seed",
        str(args.master_seed),
        "--s",
        "0.5",
        "--alphas-u",
        "0",
        "--out",
        f"{OUT}/raw",
        "--prefix",
        "pertraw",
    ]
    print("[gen] " + " ".join(gen))
    subprocess.run(gen, check=True)

    kick_children = np.random.SeedSequence([args.master_seed, 1]).spawn(len(POINTS))
    rows, sign_rows = [], []
    for j, (pt, k) in enumerate(POINTS):
        xa = x_ref[ia] + k * sig_a
        starts = {}
        # W
        xw = x_ref.copy()
        xw[ia] = xa
        starts["W"] = (xw, {})
        # R
        with h5py.File(f"{OUT}/raw/pertraw_{j:03d}.hdf5", "r") as f:
            xr = f["x"][...].astype(np.float64)
            nr = f["parms"][...].astype(str)
        assert np.array_equal(nr, names), "generator parms order differs"
        assert xr[ia] == x_ref[ia], "generator moved alphaS despite --alphas-u 0"
        xr = xr.copy()
        xr[ia] = xa
        starts["R"] = (xr, {"raw": f"raw/pertraw_{j:03d}.hdf5"})
        # K
        rng = np.random.default_rng(kick_children[j])
        signs = rng.choice([-1.0, 1.0], size=len(kick_idx))
        xk = x_ref.copy()
        xk[kick_idx] = x_ref[kick_idx] + args.kick * signs * sig[kick_idx]
        xk[ia] = xa
        starts["K"] = (xk, {})
        sign_rows.append(
            {
                "postfix": f"PROF{pt}K",
                **{names[i]: int(s) for i, s in zip(kick_idx, signs)},
            }
        )

        for st, (x, extra) in starts.items():
            pf = f"PROF{pt}{st}"
            path = f"{OUT}/{pf}.hdf5"
            d = x - x_ref
            dz = d / sig
            mask = np.ones(len(names), bool)
            mask[ia] = False
            G.write_seed(
                path,
                names,
                x,
                dict(
                    reference=REF,
                    point=pt,
                    k=k,
                    start=st,
                    master_seed=args.master_seed,
                    kick=args.kick,
                    writer="make_profile_seeds.py (rabbit.snapshot.write_snapshot)",
                ),
            )
            with h5py.File(path, "r") as f:
                xb = f["x"][...]
            dka = (xb[ia] - x_ref[ia]) / sig_a
            assert abs(dka - k) < 1e-12, (pf, dka)
            row = dict(
                postfix=pf,
                point=pt,
                k=k,
                start=st,
                seed=path,
                alphaS_offset_over_sigma=f"{dka:+.15f}",
                norm_dtheta_over_sigpost_nonalphaS=float(np.linalg.norm(dz[mask])),
                max_abs_dtheta_over_sigpost_nonalphaS=float(np.max(np.abs(dz[mask]))),
                norm_kickblock=float(np.linalg.norm(dz[kick_idx])),
                quad_cost_est=float(0.5 * d @ Cinv @ d),
                **extra,
            )
            rows.append(row)
            print(
                f"[seed] {pf}: k={k:+g} (check {dka:+.3e}) ||dz||_nonaS={row['norm_dtheta_over_sigpost_nonalphaS']:.3f} "
                f"||dz||_pdf+tnp={row['norm_kickblock']:.3f} quadratic start cost ~{row['quad_cost_est']:.1f}"
            )

    cols = [
        "postfix",
        "point",
        "k",
        "start",
        "seed",
        "alphaS_offset_over_sigma",
        "norm_dtheta_over_sigpost_nonalphaS",
        "max_abs_dtheta_over_sigpost_nonalphaS",
        "norm_kickblock",
        "quad_cost_est",
        "raw",
    ]
    for p in (f"{OUT}/manifest_profile.csv", f"{TASK}/seeds/manifest_profile.csv"):
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})
    scols = ["postfix"] + list(names[kick_idx])
    for p in (
        f"{OUT}/manifest_kick_signs.csv",
        f"{TASK}/seeds/manifest_kick_signs.csv",
    ):
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=scols)
            w.writeheader()
            w.writerows(sign_rows)
    # postfit sigma of the kicked block (nuisances, not blinded)
    with open(f"{TASK}/seeds/kick_block_sigma_post.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["param", "sigma_post_NOMSTIFF", "kick_abs"])
        for i in kick_idx:
            w.writerow([names[i], f"{sig[i]:.6g}", f"{args.kick * sig[i]:.6g}"])
    print(f"[out] {len(rows)} seeds in {OUT}; manifests copied to {TASK}/seeds/")


if __name__ == "__main__":
    main()
