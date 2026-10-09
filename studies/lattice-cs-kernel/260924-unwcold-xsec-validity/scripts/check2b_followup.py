"""Follow-up to check2 (same cache/build; alpha_s ALWAYS at the cache anchor, never read):
* fitB with lambda4 = 0 exactly and lambda4 > 0 (is the tiny negative lambda4 = -2.5e-5 involved?)
* AD vs FD for lambda4 / delta_lambda2 at fitB with steps that do not cross lambda4 = 0 (h = 1e-5, 1e-6)
* selfB  : the FULL CCCOLDSELF tune (NP+TNP+PDF+transition), alpha_s anchor
* wallB  : LATL4ZWALLCOLD tune from its main-fit snapshot (07:37, near-final), alpha_s anchor
* fine scan L2(|Y|=2.5) in [-0.030, -0.035] via delta_lambda2 (lambda2 at fit)
"""

import os, sys, time

os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")
import h5py
import numpy as np
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import params as adp
from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CACHE = f"{CEPH}/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLIND = "alphaS"
PDFS = 0.607903
NP = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]


def theta_fit(fn):
    h = io_tools.get_fitresult(fn)["parms"].get()
    return {str(n): float(v) for n, v in zip(h.axes[0], h.values()) if str(n) != BLIND}


def theta_snap(fn):
    with h5py.File(fn, "r") as f:
        names = [
            n.decode() if isinstance(n, bytes) else str(n) for n in f["parms"][...]
        ]
        x = f["x"][...]
    return {n: float(v) for n, v in zip(names, x) if n != BLIND}


t0 = time.time()
core = ScetlibADXsec(f"{CACHE}/cache.conf", f"{CACHE}/cache.npz", threads=64)
rn = [adp.rabbit_name(s) for s in core.param_names]
ri = {r: i for i, r in enumerate(rn)}
anchor = np.asarray(core.anchor, dtype=np.float64).copy()


def phys(r, th):
    spec = adp.reparam(r)
    a = anchor[ri[r]]
    if spec is None:
        return th * (PDFS if r.startswith("pdfEig") else 1.0)
    k, c = spec
    return (
        a + c[0] * th
        if k == "unit"
        else (c[0] + c[1] * th + c[2] * th * th if k == "quad" else np.exp(c[0] * th))
    )


def vec(th):
    v = anchor.copy()
    for r, t in th.items():
        if r in ri and r != BLIND:
            v[ri[r]] = phys(r, t)
    assert v[ri[BLIND]] == anchor[ri[BLIND]]
    return v


def vj(p):
    v, J = core.values_and_jacobian(p)
    return np.asarray(v, float), np.asarray(J, float)


res = {}


def run(key, p, cols=(), hs=(1e-4,)):
    t = time.time()
    v, J = vj(p)
    res[f"{key}__sigma"] = v
    res[f"{key}__p"] = p
    for c in cols:
        i = ri[c]
        res[f"{key}__J__{c}"] = J[:, i]
        for h in hs:
            pp, pm = p.copy(), p.copy()
            pp[i] += h
            pm[i] -= h
            res[f"{key}__fwd{h:g}__{c}"] = (vj(pp)[0] - v) / h
            res[f"{key}__bwd{h:g}__{c}"] = (v - vj(pm)[0]) / h
    L2 = p[ri["lambda2"]] + 6.25 * p[ri["delta_lambda2"]]
    print(
        f"[{key}] {time.time()-t:.0f}s L2(2.5)={L2:+.4f} NP={ {n: round(float(p[ri[n]]),5) for n in NP} } minσ={v.min():.4g} n≤0={(v<=0).sum()}",
        flush=True,
    )


fitB = vec(
    theta_fit(
        f"{CEPH}/260923_lattice_fits/l4zero_unwalled/fitresults_LATL4ZUNWCOLD.hdf5"
    )
)
run("fitB", fitB, cols=("lambda4", "delta_lambda2", "lambda2"), hs=(1e-4, 1e-5, 1e-6))
for l4 in [0.0, 0.001, 0.01, 0.05, 0.087]:
    p = fitB.copy()
    p[ri["lambda4"]] = l4
    run(f"fitB_l4_{l4:g}", p, cols=("lambda4", "delta_lambda2"), hs=(1e-5,))
run(
    "selfB",
    vec(theta_fit(f"{CEPH}/260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5")),
    cols=("lambda4", "delta_lambda2", "lambda2"),
    hs=(1e-5,),
)
try:
    run(
        "wallB",
        vec(
            theta_snap(
                f"{CEPH}/260923_lattice_fits/l4zero_walled/snapshot_fitresults_LATL4ZWALLCOLD.hdf5"
            )
        ),
        cols=("lambda4", "delta_lambda2", "lambda2"),
        hs=(1e-5,),
    )
except Exception as e:
    print("wallB FAILED", type(e).__name__, e)
for L2 in [-0.031, -0.032, -0.033, -0.034]:
    p = fitB.copy()
    p[ri["delta_lambda2"]] = (L2 - p[ri["lambda2"]]) / 6.25
    run(f"fine_dl2_{L2:+.3f}", p)
np.savez(
    os.path.join(OUT, "check2b_followup.npz"),
    bins=np.asarray(core.bins),
    param_names=np.array(rn),
    **res,
)
print(f"CHECK2B_DONE {time.time()-t0:.0f}s")
