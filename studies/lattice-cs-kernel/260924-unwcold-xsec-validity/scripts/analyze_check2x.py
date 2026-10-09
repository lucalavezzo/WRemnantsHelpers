"""Metrics from check2b_followup.npz (+ anchor / L2=0 reference from check2_model_eval.npz)."""

import json, os, re, sys
import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(f"{T}/" + (sys.argv[1] if len(sys.argv) > 1 else "check2b_followup.npz"))
d0 = np.load(f"{T}/check2_model_eval.npz")
b = d["bins"]
anc = d0["anchor__sigma"]
ref0 = d0["scan_dl2_+0.000__sigma"]
Yb = np.unique(b[:, 2:4], axis=0)


def row(v, iy):
    m = b[:, 2] == Yb[iy][0]
    o = np.argsort(b[m, 4])
    return b[m, 4][o], v[m][o]


def osc(v, qmax=10):
    best = (0, None)
    for iy in range(len(Yb)):
        q, r = row(v / anc, iy)
        r = r[q < qmax]
        x = np.abs(r[2:] - 2 * r[1:-1] + r[:-2]).max()
        if x > best[0]:
            best = (float(x), Yb[iy].tolist())
    return best


keys = sorted({k.split("__")[0] for k in d.files if k.endswith("__sigma")})
fwd = (b[:, 2] == 2.0) & (b[:, 4] == 0.0)
out = {}
for k in keys:
    v = d[f"{k}__sigma"]
    o = dict(
        min_sigma=float(v.min()),
        n_nonpos=int((v <= 0).sum()),
        osc=osc(v),
        fwd_bin0_over_L2zero=float(v[fwd][0] / ref0[fwd][0]),
        fwd_lowqt=[round(float(x), 3) for x in row(v, 10)[1][:6]],
        y18_lowqt=[round(float(x), 3) for x in row(v, 9)[1][:6]],
    )
    for jk in [x for x in d.files if x.startswith(k + "__J__")]:
        c = jk.split("__")[2]
        J = d[jk]
        s = np.abs(J).max()
        for fk in [
            x for x in d.files if x.startswith(k + "__fwd") and x.endswith("__" + c)
        ]:
            h = fk.split("__")[1][3:]
            f = d[fk]
            bb = d[f"{k}__bwd{h}__{c}"]
            cen = 0.5 * (f + bb)
            den = np.maximum(np.abs(J), 1e-3 * s)
            o[f"{c}_h{h}"] = dict(
                ad_vs_cfd=float(np.abs(cen - J).max() / s),
                fwd_vs_bwd=float(np.abs(f - bb).max() / s),
                worst_bin_rel=float((np.abs(cen - J) / den).max()),
                fwd_bin0_rel=float(abs(cen[fwd][0] - J[fwd][0]) / den[fwd][0]),
            )
    out[k] = o
    print(k, json.dumps(o))
print(
    "reference anchor fwd low qT",
    [round(float(x), 3) for x in row(anc, 10)[1][:6]],
    " L2=0:",
    [round(float(x), 3) for x in row(ref0, 10)[1][:6]],
)
json.dump(
    out,
    open(f"{T}/" + (sys.argv[2] if len(sys.argv) > 2 else "check2b_summary.json"), "w"),
    indent=1,
)
