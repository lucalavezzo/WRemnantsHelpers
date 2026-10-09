#!/usr/bin/env python3
"""Follow-up to spectra.py: (a) which directions stay badly conditioned after full whitening by H_s; (b) the same with
the lambda4_nu wall curvature (engaged at the end, slack at the start) added to the reference, i.e. what a
preconditioner rebuilt once that face engages would see; (c) CG counts for both. Writes spectra_extra.json.
"""
import importlib.util
import json
import os

import numpy as np

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("sp", f"{T}/scripts/spectra.py")
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)
S, E = sp.load("hess_start.npz"), sp.load("hess_end.npz")
names = S["names"].astype(str)
Hs, He, gs = S["H"], E["H"], S["g"]
n = len(names)
il4 = int(np.nonzero(names == "lambda4_nu")[0][0])
res = {}
brand = np.random.default_rng(7).standard_normal(n)
for lab, Href in [
    ("full_from_H_s", Hs),
    (
        "full_from_H_s_plus_l4nu_wall",
        Hs + np.outer(np.eye(n)[il4], np.eye(n)[il4]) * (He[il4, il4] - Hs[il4, il4]),
    ),
]:
    Tm = sp.spectral_inv_sqrt(Href)
    A = Tm.T @ He @ Tm
    w, Q = np.linalg.eigh(0.5 * (A + A.T))
    o = np.argsort(-np.abs(np.log(np.abs(w))))[:6]
    out = [
        dict(
            lam=float(w[i]),
            comp_theta=sp.top_comp(
                Tm @ Q[:, i] / np.linalg.norm(Tm @ Q[:, i]), names, 4
            ),
        )
        for i in o
    ]
    res[lab] = dict(
        kappa=float(np.abs(w).max() / np.abs(w).min()),
        n_outside_0p1_10=int(((np.abs(w) < 0.1) | (np.abs(w) > 10)).sum()),
        outliers=out,
        cg_late=sp.cg_counts(0.5 * (A + A.T), brand),
    )
    print(lab, res[lab]["kappa"], res[lab]["n_outside_0p1_10"], res[lab]["cg_late"])
    for x in out:
        print("   ", x)
json.dump(res, open(f"{T}/spectra_extra.json", "w"), indent=1)
