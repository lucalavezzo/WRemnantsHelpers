#!/usr/bin/env python3
"""Load the 4-bin probe caches (one per Q window) and print sigma and the two
small-b NP Jacobian columns at the anchor: d sigma / d lambda2_nu (CS kernel,
np_gnu_lambda2) and d sigma / d Lambda2 (TMD, np_eff_lambda2).  Feasibility
check only: shows a Q-split cache loads and yields per-Q-window J rows for the
forecast.  NOT the forecast (no stat weights, no profiling, 4 bins)."""
import time

import numpy as np

from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

D = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_probe_260923"
for tag in ["t_q60_76", "t_q76_86", "t_q86_96", "t_q96_106", "t_q106_120", "t_q60_120"]:
    t0 = time.time()
    core = ScetlibADXsec(f"{D}/{tag}/cache.conf", f"{D}/{tag}/cache.npz", threads=16)
    tl = time.time() - t0
    t0 = time.time()
    val, jac = core.values_and_jacobian(core.anchor)
    tj = time.time() - t0
    names = list(core.param_names)
    inu, itmd, ias = (
        names.index("np_gnu_lambda2"),
        names.index("np_eff_lambda2"),
        names.index("alphas"),
    )
    r = jac[:, inu] / jac[:, itmd]
    print(
        f"{tag:12s} load {tl:5.1f}s vj {tj:6.1f}s  sum {val.sum():.5g} pb  "
        f"bins {core.n_bins}  P {core.n_params}"
    )
    for b in range(core.n_bins):
        print(
            f"   bin {b}: sigma {val[b]:.4g}  dS/dl2nu/S {jac[b, inu] / val[b]:+.4f}  "
            f"dS/dL2/S {jac[b, itmd] / val[b]:+.4f}  ratio {r[b]:+.4f}  "
            f"dS/das/S {jac[b, ias] / val[b]:+.3f}"
        )
