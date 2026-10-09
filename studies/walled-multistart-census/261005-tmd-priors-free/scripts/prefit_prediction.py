#!/usr/bin/env python3
"""Pre-launch record: where NOMSTIFF sits relative to the TMD priors, and the one-Newton-step prediction of
removing them.

Priors (SCETlibADParamModel, params.REPARAM "unit"): theta ~ N(0,1), physical = anchor + 0.5*theta, anchor
from the card's theory-correction runcard (lambda2 = 0.4, lambda4 = 0.4, delta_lambda2 = 0; also the cache anchor).

Prediction: L_free = L_nom - 1/2 sum_TMD theta^2. At x_nom grad L_nom = 0, so grad L_free = -P x_nom and
H_free = H_nom - P (P = 1 on the three TMD thetas). One Newton step: dx = H_free^{-1} P x_nom, with
H_nom = C_nom^{-1} (NOMSTIFF postfit cov, includes the tau-8 wall curvature). Exact if L is quadratic.
BLINDED: alphaS only as a difference in units of sigma_NOM.
"""
import json
import sys

import numpy as np
from rabbit import io_tools

REF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
TMD = {"lambda2": (0.4, 0.5), "lambda4": (0.4, 0.5), "delta_lambda2": (0.0, 0.5)}
CS = {"lambda2_nu": (0.15, 0.1)}

fr = io_tools.get_fitresult(REF, None)
h = fr["parms"].get()
names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
x = np.asarray(h.values(), float)
C = np.asarray(fr["cov"].get().values(), float)
sig = np.sqrt(np.diag(C))
ia = names.index("alphaS")
it = [names.index(n) for n in TMD]
out = {"nll_NOM": float(fr["nllvalreduced"]), "edm_NOM": float(fr["edmval"])}

prior_term = 0.5 * float(np.sum(x[it] ** 2))
out["half_sum_theta2_TMD_at_NOM"] = prior_term
rows = {}
for n, i in zip(TMD, it):
    a, w = TMD[n]
    rows[n] = dict(
        theta=x[i],
        sigma_theta=sig[i],
        phys=a + w * x[i],
        sigma_phys=w * sig[i],
        prior_center=a,
        prior_width=w,
        pull_vs_prior=x[i],  # (phys - anchor)/width
        post_over_prior=sig[i],
        rho_alphaS=C[i, ia] / (sig[i] * sig[ia]),
    )
for n, (a, w) in CS.items():
    i = names.index(n)
    rows[n] = dict(
        theta=x[i],
        sigma_theta=sig[i],
        phys=a + w * x[i],
        sigma_phys=w * sig[i],
        rho_alphaS=C[i, ia] / (sig[i] * sig[ia]),
    )
out["lambdas_NOM"] = rows

H = np.linalg.inv(C)
H = 0.5 * (H + H.T)
P = np.zeros_like(H)
for i in it:
    P[i, i] = 1.0
Hf = H - P
ev = np.linalg.eigvalsh(Hf[np.ix_(it + [ia], it + [ia])])
g = np.zeros(len(x))
g[it] = x[it]
dx = np.linalg.solve(Hf, g)
Cf = np.linalg.inv(Hf)
sf = np.sqrt(np.diag(Cf))
out["pred"] = dict(
    dalphaS_over_sigNOM=float(dx[ia] / sig[ia]),
    sig_alphaS_ratio=float(sf[ia] / sig[ia]),
    dNLL_pred=float(-0.5 * g @ dx),  # second-order: L_free(x_nom+dx) - L_free(x_nom)
    lambdas={
        n: dict(
            phys=TMD[n][0] + TMD[n][1] * (x[i] + dx[i]),
            sigma_phys=TMD[n][1] * sf[i],
            dphys=TMD[n][1] * dx[i],
            dtheta_over_sigNOM=dx[i] / sig[i],
            rho_alphaS=Cf[i, ia] / (sf[i] * sf[ia]),
        )
        for n, i in zip(TMD, it)
    },
    lambda2_nu=dict(
        dphys=0.1 * dx[names.index("lambda2_nu")],
        sigma_phys=0.1 * sf[names.index("lambda2_nu")],
    ),
    min_eig_Hfree_TMDblock=float(ev.min()),
)
top = np.argsort(-np.abs(dx / sig))[:10]
out["pred"]["top_moves_over_sigNOM"] = [(names[i], float(dx[i] / sig[i])) for i in top]
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
