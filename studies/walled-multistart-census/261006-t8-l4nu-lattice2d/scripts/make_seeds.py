#!/usr/bin/env python3
"""Seeds for T8 on the 2D-lattice card (flat x+parms, rabbit.snapshot.write_snapshot; no cov, so --noHessian loads).
  A: NOMSTIFF's vector + lambda4_nu theta = 0 (physical 0: ON the lambda4_nu >= 0 boundary; NOMSTIFF also sits 9.2e-7
     past the L2(|Y|=2.5) face, so the start is not strictly feasible anyway -- scipy accepts an infeasible x0,
     see trust-constr-nominal/261006-tc-from-C).
  B: XWSTIFF's vector (the W point) BY NAME. Checks: the name SETS of XWSTIFF and of the target (NOMSTIFF + lambda4_nu)
     are identical; same base card A (2D card = card A + external term only), so identical anchors and data_obs ->
     identical alphaS blinding offset (cf. 261005-cold-min-restart/scripts/make_seeds.py, blinding_check.py).
Prints only differences / sigma units for alphaS."""
import json
import os
import sys

import h5py
import numpy as np
from rabbit import io_tools, snapshot

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
from wremnants.postprocessing.scetlib_ad import params as P  # noqa: E402
from wremnants.postprocessing.scetlib_ad import response as R  # noqa: E402


def load(path):
    fr, meta = io_tools.get_fitresult(path, None, meta=True)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    return (
        names,
        np.asarray(h.values(), float),
        np.sqrt(np.asarray(h.variances(), float)),
        R.corr_config_from_meta(meta)["config"],
    )


nN, xN, sN, cfgN = load(C.NOMSTIFF)
nW, xW, sW, cfgW = load(C.XWSTIFF)
tgt = nN + ["lambda4_nu"]
assert set(tgt) == set(nW), set(tgt) ^ set(nW)
for n in nW:
    if P.corr_anchor_key(n) is not None:
        assert P.corr_anchor_value(cfgN, n) == P.corr_anchor_value(cfgW, n), n
os.makedirs(f"{C.OUT}/seeds", exist_ok=True)
rep = {}
xa = np.concatenate([xN, [0.0]])
pa = f"{C.OUT}/seeds/seed_A_NOMSTIFF_l4nu0.hdf5"
iW = {n: i for i, n in enumerate(nW)}
xb = np.array([xW[iW[n]] for n in tgt])
pb = f"{C.OUT}/seeds/seed_B_XWSTIFF_in_2D.hdf5"
# A2 (relaunch 10:15): as A but lambda4_nu = +1e-4 physical (theta 2e-4), strictly inside the lambda4_nu face
xa2 = np.concatenate([xN, [2e-4]])
pa2 = f"{C.OUT}/seeds/seed_A2_NOMSTIFF_l4nu1e-4.hdf5"
# P (Luca's plan 10:20): census pert_000 (NOMSTIFF frame, 3719 names, same order) + lambda4_nu ~ U[0, 0.01] physical
PERT = f"{C.A}/261001_census_nominal/seeds/pert_000.hdf5"
with h5py.File(PERT, "r") as f:
    xp, npn = f["x"][...], list(f["parms"][...].astype(str))
assert npn == nN, "pert_000 layout != NOMSTIFF"
u4 = float(np.random.default_rng(20261006).uniform(0.0, 0.01))
xp2 = np.concatenate([xp, [u4 / 0.5]])
pp = f"{C.OUT}/seeds/seed_P_pert000_l4nuU.hdf5"
print(f"[seed P] lambda4_nu = {u4:.6f} (rng 20261006)")
for p, x, src in [
    (pa, xa, C.NOMSTIFF),
    (pb, xb, C.XWSTIFF),
    (pa2, xa2, C.NOMSTIFF),
    (pp, xp2, PERT),
]:
    if os.path.exists(p) and p not in (pa2, pp):
        with h5py.File(p, "r") as f:
            assert np.array_equal(f["x"][...].view(np.uint64), x.view(np.uint64)), p
        continue
    snapshot.write_snapshot(
        p,
        np.array(tgt),
        x,
        meta=dict(source=src, rule="by-name onto NOMSTIFF names + lambda4_nu"),
    )
    with h5py.File(p, "r") as f:
        assert (
            np.array_equal(f["x"][...].view(np.uint64), x.view(np.uint64))
            and list(f["parms"][...].astype(str)) == tgt
        )
        assert "cov" not in f
ia = tgt.index("alphaS")
d = (xb[:-1] - xN) / sN
dP = (xp - xN) / sN
rep = dict(
    seed_P=pp,
    P_lambda4_nu_phys=u4,
    P_dalphaS_over_sigNOM=float(dP[ia]),
    P_norm_dtheta_over_sigNOM=float(np.linalg.norm(dP)),
    seed_A=pa,
    seed_B=pb,
    n=len(tgt),
    anchors_equal=True,
    B_dalphaS_over_sigNOM=float(d[ia]),
    B_norm_dtheta_over_sigNOM=float(np.linalg.norm(d)),
    B_lambda4_nu_phys=float(0.5 * xb[-1]),
    B_lambda2_nu_phys=float(0.15 + 0.1 * xb[tgt.index("lambda2_nu")]),
)
print(rep)
json.dump(rep, open(f"{C.TASK}/seeds.json", "w"), indent=1)
