#!/usr/bin/env python3
"""Extract sigma and the full SCETlib-AD Jacobian from each grid-A Q-window cache.

For every window cache (qsplit_260923/q<lo>_<hi>) and every evaluation point:
  * values, jacobian (physical parameter units) via ScetlibADXsec.values_and_jacobian
  * the two mu_R envelope legs (kappa_R = 0.5, 2 at kappa_F = 1), always at the ANCHOR
    (the param model freezes the envelope at the anchor; scale_envelope.py)
  * a central finite-difference check of the NP columns at that point (value function
    only), because an AD derivative correct at the anchor says nothing away from it
    (knowledge/20_frameworks/scetlib_diff_scales_caveats.md).

fo_muf_poly = 0: kappa_F frozen and the 3-point envelope does not move it, the two
conditions of SCETlibADParamModel._check_fo_muf_poly.

Writes jacobians.npz in the task dir (a few hundred kB).
"""
import argparse
import os

import numpy as np

from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDIR = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_260923"
WINDOWS = [(60, 76), (76, 86), (86, 96), (96, 106), (106, 120)]
NP = [
    "np_eff_lambda2",
    "np_eff_lambda4",
    "np_eff_delta_lambda2",
    "np_gnu_lambda2",
    "np_gnu_lambda4",
]
# lattice best fit at lambda_inf_nu = 2 (260923-scetlib-kernel-fit): 0.184(38), -0.0059(33).
# The full lattice point (lambda4_nu = -0.0059) is NOT evaluable on this cache: for lambda4_nu < 0
# the cached value function is erratic (one-sided FDs at h = 1e-4 disagree by 20-100 %, low-qT
# sigma goes negative at -0.01) -- see diag_np_fd.out. So the robustness point keeps the
# lattice lambda2_nu and puts lambda4_nu on its physical boundary, 0.
POINTS = {"anchor": {}, "lattice": {"np_gnu_lambda2": 0.184, "np_gnu_lambda4": 0.0}}
# (step, one-sided?): lambda4_nu is FORWARD only -- the lambda4_nu < 0 side is the pathological one.
FD_STEP = {
    "np_eff_lambda2": (0.01, False),
    "np_eff_lambda4": (0.01, False),
    "np_eff_delta_lambda2": (0.01, False),
    "np_gnu_lambda2": (0.001, False),
    "np_gnu_lambda4": (1e-4, True),
}

ap = argparse.ArgumentParser()
ap.add_argument("--threads", type=int, default=16)
ap.add_argument("--out", default=os.path.join(TASK, "jacobians.npz"))
args = ap.parse_args()

out = {}
for lo, hi in WINDOWS:
    tag = f"q{lo}_{hi}"
    core = ScetlibADXsec(
        f"{CDIR}/{tag}/cache.conf",
        f"{CDIR}/{tag}/cache.npz",
        threads=args.threads,
        fo_muf_poly=0,
    )
    names = list(core.param_names)
    out["names"] = np.array(names)
    out[f"{tag}_bins"] = core.bins
    out["anchor"] = core.anchor
    ikr = names.index("scale_kappa_R")
    for leg, kr in (("kr05", 0.5), ("kr2", 2.0)):
        p = core.anchor.copy()
        p[ikr] = kr
        v, _ = core.values_and_jacobian(p)
        out[f"{tag}_{leg}"] = np.asarray(v)
    for pname, over in POINTS.items():
        p = core.anchor.copy()
        for k, v in over.items():
            p[names.index(k)] = v
        val, jac = core.values_and_jacobian(p)
        val, jac = np.asarray(val), np.asarray(jac)
        out[f"{tag}_{pname}_val"] = val
        out[f"{tag}_{pname}_jac"] = jac
        out[f"{pname}_p"] = p
        fd = np.zeros((len(val), len(NP)))
        for j, k in enumerate(NP):
            h, fwd = FD_STEP[k]
            i = names.index(k)
            pp = p.copy()
            pp[i] += h
            pm = p.copy()
            if not fwd:
                pm[i] -= h
            fd[:, j] = (
                np.asarray(core.values_and_jacobian(pp)[0])
                - np.asarray(core.values_and_jacobian(pm)[0])
            ) / (pp[i] - pm[i])
        out[f"{tag}_{pname}_fd"] = fd
        ad = jac[:, [names.index(k) for k in NP]]
        rel = np.abs(fd - ad).max(0) / np.abs(ad).max(0)
        print(
            f"{tag} {pname}: sigma {val.sum():.5g} pb, bins {len(val)}; FD vs AD max|d|/max|J| per NP col: "
            + " ".join(f"{k.split('_',1)[1]}={r:.1e}" for k, r in zip(NP, rel)),
            flush=True,
        )
np.savez(args.out, **out)
print("wrote", args.out)
