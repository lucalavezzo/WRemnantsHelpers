#!/usr/bin/env python3
"""NOMTMDFREE vs NOMSTIFF (same card/cache/wall; NOMTMDFREE has no Gaussian priors on lambda2, lambda4, delta_lambda2).

Reports (BLINDED: alphaS only as a difference in sigma_NOM; no absolute alphaS anywhere):
  * NLL (nllvalreduced), EDM; NLL comparability: rabbit's prior term is exactly 1/2 cw (x - x0)^2 with x0 = 0, cw = 1 for
    the three TMD thetas (fitter._compute_lc; NOMSTIFF.log "lambda2: mu=0 sigma=1"), so NOMSTIFF re-evaluated without
    the TMD priors at its own point is EXACTLY NLL_NOM - 1/2 sum theta_TMD^2;
  * physical NP lambdas with sigma (anchor + width*theta), d(alphaS)/sigma_NOM, sigma ratio, rho(alphaS, lambda);
  * active wall faces (analyze_census.faces, margin 0);
  * largest |dtheta/sigma_NOM| movers, per-family norms;
  * cache validity: |d lambda| from the cache anchor in prior widths (0.5).
Also writes cov json for np_function_plots (physical lambdas + cov).
usage (container): compare.py <fitresult_free> <out.json>
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CENS = os.path.join(HERE, "../../261001-census-nominal/scripts")
sys.path.insert(0, os.path.abspath(CENS))
import analyze_census as AC  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as W  # noqa: E402
from wremnants.postprocessing.scetlib_ad import response as R  # noqa: E402
from rabbit import io_tools  # noqa: E402

REF = AC.REF
FREE = sys.argv[1]
OUTJ = sys.argv[2]
TMD = ["lambda2", "lambda4", "delta_lambda2"]
WID = {"lambda2": 0.5, "lambda4": 0.5, "delta_lambda2": 0.5, "lambda2_nu": 0.1}


def full(path):
    fit = AC.load_fit(path)
    fr = io_tools.get_fitresult(path, None)
    fit["cov"] = np.asarray(fr["cov"].get().values(), float)
    return fit


ref, fre = full(REF), full(FREE)
assert ref["names"] == fre["names"]
names = ref["names"]
cfg = R.corr_config_from_meta(ref["meta"])["config"]
np_model, np_model_nu = W.forms_from_corr_config(cfg)
lam_names = tuple(dict.fromkeys(W._TMD_LAMBDAS[np_model] + W._CS_LAMBDAS[np_model_nu]))
ia = names.index("alphaS")
out = {}
for tag, f in (("NOMSTIFF", ref), ("NOMTMDFREE", fre)):
    ph, fitted = AC.physical(f, cfg, lam_names)
    fc = AC.faces(ph, fitted, np_model, np_model_nu)
    C = f["cov"]
    s = np.sqrt(np.diag(C))
    lam = {}
    for n in fitted:
        i = names.index(n)
        lam[n] = dict(
            phys=ph[n],
            sigma=WID.get(n, 1.0) * s[i],
            theta=f["x"][i],
            rho_alphaS=C[i, ia] / (s[i] * s[ia]),
            dist_from_anchor_in_REPARAM_widths=(ph[n] - AC.P.corr_anchor_value(cfg, n))
            / WID[n],
        )
    rho_tmd = {
        f"{a}|{b}": C[names.index(a), names.index(b)]
        / (s[names.index(a)] * s[names.index(b)])
        for k, a in enumerate(fitted)
        for b in fitted[k + 1 :]
    }
    half_th2 = 0.5 * sum(f["x"][names.index(n)] ** 2 for n in TMD)
    out[tag] = dict(
        nll=f["nll"],
        edm=f["edm"],
        half_sum_theta2_TMD=half_th2,
        lambdas=lam,
        rho_lambda_lambda=rho_tmd,
        faces=[
            dict(label=AC.short(r["label"]), coeff=r["coeff"], on=bool(r["on"]))
            for r in fc
        ],
    )
    idx = [names.index(n) for n in fitted]
    w = np.array([WID[n] for n in fitted])
    json.dump(
        dict(
            names=list(fitted),
            mu=[ph[n] for n in fitted],
            cov=(C[np.ix_(idx, idx)] * np.outer(w, w)).tolist(),
        ),
        open(os.path.join(os.path.dirname(OUTJ), f"cov_{tag}.json"), "w"),
        indent=1,
    )

sr, sf = np.sqrt(np.diag(ref["cov"])), np.sqrt(np.diag(fre["cov"]))
dx = (fre["x"] - ref["x"]) / sr
out["dalphaS_over_sigNOM"] = dx[ia]
out["sig_alphaS_ratio"] = sf[ia] / sr[ia]
out["nll_free"] = fre["nll"]
out["nll_NOM_minus_TMDprior"] = ref["nll"] - out["NOMSTIFF"]["half_sum_theta2_TMD"]
out["dNLL_free_vs_NOMnoprior"] = out["nll_free"] - out["nll_NOM_minus_TMDprior"]
top = np.argsort(-np.abs(dx))[:15]
out["top_movers_over_sigNOM"] = [(names[i], dx[i]) for i in top]
fam = np.array([AC.family(n) for n in names])
out["dtheta_sig_family"] = {
    lab: float(np.linalg.norm(dx[fam == lab])) for lab, _ in AC.FAMILIES
}
out["dtheta_sig_total"] = float(np.linalg.norm(dx))
sig_ratio_top = np.argsort(-np.abs(np.log(sf / sr)))[:8]
out["largest_sigma_ratio_changes"] = [(names[i], sf[i] / sr[i]) for i in sig_ratio_top]
json.dump(out, open(OUTJ, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
