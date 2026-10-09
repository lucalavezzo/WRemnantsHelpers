"""Read the CS (gamma_nu) lambdas from the scetlib_ad real-data fits of card A
(studies/alphas-scan-discontinuity). The AD model stores lambdas as THETA with
physical = anchor + width*theta (scetlib_ad/params.py REPARAM, 'unit' kind), so the
scetlib_np reader fitresult_lambdas (which assumes physical parms) does NOT apply;
this is the minimal reader. Anchor = cache.conf [Nonperturbative] of
scetlib_ad_caches/pdf62_corrgrid_260827/merged_full. alphaS is NOT read out."""

import json, os
import numpy as np
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import params as P

B = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
RUNS = [
    (
        "unwalled, main min (warm) CCKRYLOVWARM",
        f"{B}/260917_cc_fits_hvpfix/fitresults_CCKRYLOVWARM.hdf5",
    ),
    (
        "unwalled, second min (cold) CCCOLDSELF",
        f"{B}/260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5",
    ),
    (
        "walled, main (warm) CCWALLWARMPF",
        f"{B}/260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5",
    ),
    (
        "walled, cold-resumed CCWALLCOLDR",
        f"{B}/260917_cc_fits_wall/fitresults_CCWALLCOLDR.hdf5",
    ),
    (
        "walled, warm from unwalled 2nd CCWALLSHIFT",
        f"{B}/260917_cc_fits_wall/fitresults_CCWALLSHIFT.hdf5",
    ),
]
ANCHOR = dict(
    lambda2_nu=0.15,
    lambda4_nu=0.0,
    lambda_inf_nu=2.0,
    lambda2=0.4,
    lambda4=0.4,
    delta_lambda2=0.0,
)
NAMES = [
    "lambda2_nu",
    "lambda4_nu",
    "lambda_inf_nu",
    "lambda6_nu",
    "lambda2",
    "lambda4",
    "delta_lambda2",
]


def width(n):
    r = P.reparam(n)
    return r[1][0] if r and r[0] == "unit" else None


out = []
for lab, f in RUNS:
    fr, meta = io_tools.get_fitresult(f, None, meta=True)
    parms = fr["parms"].get()
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in parms.axes[0]]
    v = parms.values()
    var = parms.variances()
    args = (meta.get("meta_info", {}) or {}).get("args", {})
    ent = dict(
        name=lab,
        file=f,
        freeze=args.get("freezeParameters"),
        paramModel=args.get("paramModel"),
        regularization=args.get("regularization"),
        regStrength=args.get("regularizationStrength"),
        externalPostfit=args.get("externalPostfit"),
        has_cov="cov" in fr.keys(),
        params={},
    )
    idx = {n: i for i, n in enumerate(names)}
    sel = []
    for n in NAMES:
        if n not in idx:
            ent["params"][n] = "absent (frozen at anchor)" if n in ANCHOR else "absent"
            continue
        w = width(n) or 1.0
        th = float(v[idx[n]])
        sig = (
            float(np.sqrt(var[idx[n]]))
            if var is not None and var[idx[n]] > 0
            else float("nan")
        )
        ent["params"][n] = dict(
            theta=th,
            theta_sigma=sig,
            width=w,
            physical=ANCHOR.get(n, 0.0) + w * th,
            physical_sigma=w * sig,
        )
        sel.append(n)
    if ent["has_cov"]:
        cov = fr["cov"].get()
        cn = [n.decode() if isinstance(n, bytes) else str(n) for n in cov.axes[0]]
        ci = [cn.index(n) for n in sel]
        C = cov.values()[np.ix_(ci, ci)]
        W = np.array([width(n) or 1.0 for n in sel])
        ent["cov_names"] = sel
        ent["cov_physical"] = (C * np.outer(W, W)).tolist()
    out.append(ent)
    print(
        "==",
        lab,
        "freeze=",
        ent["freeze"],
        "PM=",
        ent["paramModel"],
        "reg=",
        ent["regularization"],
        ent["regStrength"],
        "cov=",
        ent["has_cov"],
    )
    for n in NAMES:
        print("   ", n, ent["params"][n])
json.dump(
    out,
    open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ad_postfits.json"),
        "w",
    ),
    indent=1,
    default=str,
)
