#!/usr/bin/env python3
"""Check the ported scetlib_ad/np_function_plots curves against the retired tool's cs_kernel/tmd_bc values.

Same fits, same forms: the postfit central curves must agree to float precision. Runs in the container from the main
WRemnants tree (no worktree on PYTHONPATH):  agent_setup.sh -- python3 check_two_panel.py
"""
import json
import os

import numpy as np

from wremnants.postprocessing.scetlib_ad import np_function_plots as NPF

H = os.path.dirname(os.path.abspath(__file__))
A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
FITS = {
    "LATFROZ_V3": f"{A}/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5",
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
}
ref = json.load(open(os.path.join(H, "two_plots/data/cs_tmd_values.json")))
bT = np.linspace(
    1e-3, 12.6, 400
)  # the retired tool's grid; values stored at its nearest nodes
worst = 0.0
for k, p in FITS.items():
    _, post, _, _ = NPF.read_ad_fitresult(p, n_toys=0)
    gz = 0.5 * NPF.gamma_nu_curve(
        bT, post.gnu
    )  # the plotter draws gamma_nu; the old cs_kernel drew gamma_zeta
    F = {y: NPF.f_eff_curve(bT, y, post.eff) for y in (0.0, 2.5)}
    for bq, row in ref.items():
        i = int(np.argmin(np.abs(bT - float(bq[2:]))))
        r = row[k]
        d = [
            abs(gz[i] - r["gz"]),
            abs(F[0.0][i] - r["F0.0"]),
            abs(F[2.5][i] - r["F2.5"]),
        ]
        worst = max(worst, *d)
        print(
            f"{k:11s} b_T={bT[i]:6.3f}  gamma_zeta^NP {gz[i]:+.6f} (old {r['gz']:+.6f})  "
            f"F(0) {F[0.0][i]:.6f} (old {r['F0.0']:.6f})  F(2.5) {F[2.5][i]:.6f} (old {r['F2.5']:.6f})"
        )
print(f"max |new - old| = {worst:.2e}")
