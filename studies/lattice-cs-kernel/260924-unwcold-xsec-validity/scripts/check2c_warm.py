"""Check 2 for LATL4ZUNWWARM (converged snapshot), alpha_s ALWAYS at the cache anchor (never read).
warmB : full warm tune (NP+TNP+PDF+transition2), FD on lambda2/delta_lambda2/lambda4 (h = 1e-5, 1e-6)
warm scans from warmB, L2(|Y|=2.5) in [+0.05, -0.15]:
   scanW_dl2 : via delta_lambda2 (lambda2 fixed at -0.078 -> L2(0) stays < 0)
   scanW_l2  : via lambda2 (delta_lambda2 fixed)
warm lambda4 scan at the warm L2: lambda4 in {0.096 .. 0}
cold tune scan extension: fitB via delta_lambda2 to L2(2.5) = -0.15 (for completeness)
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


def run(key, p, cols=(), hs=(1e-5,)):
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


warm = vec(
    theta_snap(
        f"{CEPH}/260923_lattice_fits/l4zero_unwalled_warm/snapshot_fitresults_LATL4ZUNWWARM.hdf5"
    )
)
run("warmB", warm, cols=("lambda2", "delta_lambda2", "lambda4"), hs=(1e-4, 1e-5, 1e-6))
L2T = np.round(np.arange(0.05, -0.1501, -0.01), 4)
for mode in ["dl2", "l2"]:
    for L2 in L2T:
        p = warm.copy()
        if mode == "dl2":
            p[ri["delta_lambda2"]] = (L2 - p[ri["lambda2"]]) / 6.25
        else:
            p[ri["lambda2"]] = L2 - 6.25 * p[ri["delta_lambda2"]]
        run(f"scanW_{mode}_{L2:+.3f}", p, cols=("lambda2", "delta_lambda2"), hs=(1e-5,))
for l4 in [0.06, 0.03, 0.01, 0.005, 0.002, 0.0]:
    p = warm.copy()
    p[ri["lambda4"]] = l4
    run(f"warmB_l4_{l4:g}", p, cols=("lambda4", "delta_lambda2"), hs=(1e-5,))
cold = vec(
    theta_fit(
        f"{CEPH}/260923_lattice_fits/l4zero_unwalled/fitresults_LATL4ZUNWCOLD.hdf5"
    )
)
for L2 in [-0.07, -0.10, -0.138, -0.15]:
    p = cold.copy()
    p[ri["delta_lambda2"]] = (L2 - p[ri["lambda2"]]) / 6.25
    run(f"scanC_dl2_{L2:+.3f}", p)
np.savez(
    os.path.join(OUT, "check2c_warm.npz"),
    bins=np.asarray(core.bins),
    param_names=np.array(rn),
    **res,
)
print(f"CHECK2C_DONE {time.time()-t0:.0f}s")
