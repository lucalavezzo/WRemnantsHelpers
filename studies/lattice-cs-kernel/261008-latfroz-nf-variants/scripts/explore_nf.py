"""Exploration: n_f-variant shifts from gamma_nu_points at alpha_s 0.118 / 0.1168 (public numbers only)."""

import numpy as np
from wremnants.postprocessing.scetlib_ad import xsec_backend as xb
import os

WREM = os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants")
CONF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25/cache.conf"
conf, sigma = xb.configure(CONF, threads=4)
sing, _ = sigma.sub_pieces()
names = list(sing.gradient_param_names())
print(
    "names with gnu/alphas/tnp_gamma:",
    [n for n in names if "gnu" in n or n == "alphas" or n.startswith("tnp_gamma")],
)
d = np.load(
    os.path.join(WREM, "wremnants/postprocessing/scetlib_ad/data/lattice_aswz_data.npz")
)
print("data keys", list(d.keys()))
old = np.load(
    os.path.join(
        WREM, "wremnants/postprocessing/scetlib_ad/data/lattice_aswz_inputs.npz"
    )
)
print("old keys", list(old.keys()))
bT = np.array(d["b_fm"]) * float(d["fm_to_gevinv"])
p0 = np.array(sing.gradient_central(), float)
ix = {n: i for i, n in enumerate(names)}
print(
    "anchor:", {n: p0[ix[n]] for n in names if "gnu" in n or n.startswith("tnp_gamma")}
)


def g(p, mu, nf=0, mm=0.0):
    return 0.5 * np.asarray(sing.gamma_nu_points(bT, mu, p, 0, nf, mm)["value"])


MB = 4.18
for a in (0.118, 0.1168):
    p = p0.copy()
    p[ix["alphas"]] = a
    z5 = g(p, 2.0)
    V1 = g(p, 1.0) + g(p, 2.0, 4, 1.0) - g(p, 1.0, 4, 1.0) - z5
    V2 = g(p, 1.0) + g(p, 2.0, 4, MB) - g(p, 1.0, 4, MB) - z5
    V3l = g(p, MB) + g(p, 2.0, 4, MB) - g(p, MB, 4, MB) - z5
    V3p = g(p, 2.0, 4, MB) - z5
    for k, v in (("V1", V1), ("V2", V2), ("V3lit", V3l), ("V3pure", V3p)):
        print(f"as={a} {k:7s} min {v.min():+.6f} max {v.max():+.6f}")
    if a == 0.118:
        o2 = np.array(old["pert_nf5_mu1match"]) - np.array(old["pert"])
        print(
            "old table V2-like shift",
            o2.min(),
            o2.max(),
            " native V2 / old",
            (V2 / o2).min(),
            (V2 / o2).max(),
        )
        if "pert_nf4" in old:
            o3 = np.array(old["pert_nf4"]) - np.array(old["pert"])
            print(
                "old table pure nf4 shift",
                o3.min(),
                o3.max(),
                " native V3pure / old",
                (V3p / o3).min(),
                (V3p / o3).max(),
            )
    # NP cancellation check
    q = p.copy()
    q[ix["np_gnu_lambda2"]] += 0.1
    q[ix["np_gnu_lambda4"]] += 0.01
    V3q = g(q, 2.0, 4, MB) - g(q, 2.0)
    print("pure nf4 NP-cancel max diff", np.max(np.abs(V3q - V3p)))
print("b_fm", np.array(d["b_fm"]))
