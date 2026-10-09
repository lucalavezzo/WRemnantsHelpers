#!/usr/bin/env python3
"""Vector-only (no cache load) estimate of the CMR1B - XWSTIFF NLL split: Gaussian prior (constraint) term and wall term
from the stored x; data+BB = remainder. Prior term: 0.5*sum(w*theta^2) over the card's constrained systs
(hconstraintweights; theta0 = 0 on real data) + 0.5*sum(theta^2/s^2) over the param model's constrained params
(meta 'param_priors'). Wall: exp(16)*sum relu2 (analysis.json conditions). The gated term_eval.py run is the exact check.
"""
import json, os, sys
import h5py
import numpy as np
from rabbit import io_tools

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = (
    f"{A}/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
)
F = {
    "XWSTIFF": f"{A}/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5",
    "CMR1B": f"{A}/261005_cold_min_restart/fitresults_CMR1B.hdf5",
}
with h5py.File(CARD, "r") as f:
    print("card keys:", [k for k in f.keys()][:30])
    systs = [s.decode() if isinstance(s, bytes) else str(s) for s in f["hsysts"][...]]
    cw = np.asarray(f["hconstraintweights"][...], float)
res = {}
for k, p in F.items():
    fr, meta = io_tools.get_fitresult(p, None, meta=True)
    h = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    x = dict(zip(names, np.asarray(h.values(), float)))
    pp = meta.get("param_priors")
    if k == "XWSTIFF":
        print("param_priors type:", type(pp), str(pp)[:400])
    lc_syst = 0.5 * sum(w * x[s] ** 2 for s, w in zip(systs, cw) if w > 0)
    res[k] = dict(
        lc_syst=lc_syst, names=names, x=x, pp=pp, nll=float(fr["nllvalreduced"])
    )
print("n constrained systs", int(np.sum(cw > 0)), "of", len(systs))
json.dump({k: {"lc_syst": v["lc_syst"]} for k, v in res.items()}, sys.stdout)
print()

an = json.load(open(f"{TASK}/analysis.json"))
for k, v in res.items():
    pp = v["pp"]
    pn = [n.decode() if isinstance(n, bytes) else str(n) for n in pp["params"]]
    m, sg, mu = (
        np.asarray(pp["mask"]),
        np.asarray(pp["sigmas"], float),
        np.asarray(pp["means"], float),
    )
    v["lc_pm"] = float(
        sum(0.5 * ((v["x"][n] - mu[i]) / sg[i]) ** 2 for i, n in enumerate(pn) if m[i])
    )
lp = {
    "CMR1B": float(
        np.exp(16) * sum(max(0.0, -f["coeff"]) ** 2 for f in an["CMR1B"]["faces"])
    ),
    "XWSTIFF": float(
        np.exp(16) * sum(max(0.0, -f["coeff"]) ** 2 for f in an["CMR1B"]["faces_ref"])
    ),
}
d = {t: res["CMR1B"][t] - res["XWSTIFF"][t] for t in ("nll", "lc_syst", "lc_pm")}
d["wall"] = lp["CMR1B"] - lp["XWSTIFF"]
d["data_plus_bb"] = d["nll"] - d["lc_syst"] - d["lc_pm"] - d["wall"]
out = dict(
    delta=d,
    wall=lp,
    lc_pm={k: v["lc_pm"] for k, v in res.items()},
    lc_syst={k: v["lc_syst"] for k, v in res.items()},
    note="vector-only estimate; prior = 0.5*sum theta^2 (card constraints, theta0=0) + param-model priors; data+BB = remainder",
)
json.dump(out, open(f"{TASK}/prior_split_CMR1B.json", "w"), indent=1)
print(json.dumps(d, indent=1))
