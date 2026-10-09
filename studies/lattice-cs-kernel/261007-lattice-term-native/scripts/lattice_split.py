"""NLL split of LATB8 vs NOMSTIFF with the live lattice term replaced by its value at alpha_s = 0.118 (public anchor),
and the slope dL/dalpha_s of that substitution (the size of its error per 0.001 of the blinded alpha_s offset).
Inputs: compare.json (this task). Writes lattice_split.json."""

import json, os, sys
import numpy as np

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants"))
from wremnants.postprocessing.scetlib_ad import lattice_cs_term as LT  # noqa: E402
from wremnants.postprocessing.scetlib_ad import xsec_backend as XB  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
c = json.load(open(f"{TASK}/compare.json"))
_, sig = XB.configure(
    f"{A}/ad_scetlib_caches/pdf62_y35_260921_y25/cache.conf", threads=4
)
s = sig.sub_pieces()[0]
s.set_pdf_eig_params(29)
nm = list(s.gradient_param_names())
core = LT.LatticeCSNativeCore(
    s, np.array(s.gradient_central(), float), require_rules=False
)
out = {}
for k in ("LATFULL8", "LATB8"):
    r = c[k]
    p = core.p_ref.copy()
    p[nm.index("np_gnu_lambda2")] = r["lambdas"]["lambda2_nu"]
    p[nm.index("np_gnu_lambda4")] = r["lambdas"]["lambda4_nu"]
    p[nm.index("tnp_gamma_nu")] = r["tnps"]["resumTNP_gamma_nu"]["theta"]
    p[nm.index("tnp_gamma_cusp")] = r["tnps"]["resumTNP_gamma_cusp"]["theta"]
    ia = nm.index("alphas")
    L = lambda a: 0.5 * (
        core.chi2_full(np.where(np.arange(len(p)) == ia, a, p)) - core.chi2_min
    )  # noqa: E731
    L0 = L(0.118)
    slope = (L(0.1181) - L(0.1179)) / 0.0002 * 1e-3  # per 0.001
    lumped = r["nll"] - r["wall"] - r["priors"]
    out[k] = dict(
        nll=r["nll"],
        priors=r["priors"],
        wall=r["wall"],
        data_bb_plus_live_lattice=lumped,
        lattice_at_0118=L0,
        dL_per_0p001_alphas=slope,
        data_bb_est=lumped - L0,
    )
n = c["NOMSTIFF"]
out["NOMSTIFF"] = dict(
    nll=n["nll"],
    priors=n["priors"],
    wall=n["wall"],
    lattice_1d_gauss=n["lattice"],
    data_bb=n["data_bb"],
)
for k in ("LATFULL8", "LATB8"):
    out[k]["d_data_bb_vs_NOMSTIFF_est"] = out[k]["data_bb_est"] - n["data_bb"]
json.dump(out, open(f"{TASK}/lattice_split.json", "w"), indent=1)
print(json.dumps(out, indent=1))
