"""Check 2: evaluate the production AD cache (pdf62_corrgrid_260827/merged_full, authval b66f8de)
at the LATL4ZUNWCOLD postfit NP tune with alpha_s HELD AT THE CACHE ANCHOR (theta_alphaS = 0,
i.e. 0.118 -- unblinded by construction; the fitted alpha_s is never read into the vector).

Points:
  anchor           : cache anchor (sanity baseline)
  fitA             : LATL4ZUNWCOLD NP lambdas, everything else at the anchor
  fitB             : LATL4ZUNWCOLD NP + TNPs + PDF eigs + transition2 from the fit, alphaS at anchor
  selfA            : CCCOLDSELF NP lambdas, rest at anchor (a sane-fit baseline)
  scan_dl2 / scan_l2 : from fitB, move L2(|Y|=2.5) = lambda2 + 6.25*delta_lambda2 over
                       [+0.05, -0.05] via delta_lambda2 (lambda2 fixed) or via lambda2 (dl2 fixed).
Per point: sigma on the 770 cache bins, and AD Jacobian vs central/fwd/bwd FDs on the TMD columns.
theta -> physical: exactly SCETlibADParamModel._physical (params.REPARAM; pdfEig * pdf_coeff_scale).
"""

import argparse, json, os, sys, time
import numpy as np
from rabbit import io_tools
from wremnants.postprocessing.scetlib_ad import params as adp
from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
p = argparse.ArgumentParser()
p.add_argument(
    "--cache", default=f"{CEPH}/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full"
)
p.add_argument(
    "--fit",
    default=f"{CEPH}/260923_lattice_fits/l4zero_unwalled/fitresults_LATL4ZUNWCOLD.hdf5",
)
p.add_argument(
    "--ref", default=f"{CEPH}/260917_cc_selfrestart/fitresults_CCCOLDSELF.hdf5"
)
p.add_argument("--threads", type=int, default=64)
p.add_argument("--h", type=float, default=1e-4, help="FD step (physical units)")
p.add_argument(
    "--pdf-coeff-scale",
    type=float,
    default=0.607903,
    help="from the fit log (CT18ZNNLO)",
)
p.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
args = p.parse_args()

NP = ["lambda2", "lambda4", "delta_lambda2", "lambda2_nu", "lambda4_nu"]
TMD_COLS = ["lambda2", "delta_lambda2", "lambda4"]
BLIND = "alphaS"


def read_theta(fn):
    h = io_tools.get_fitresult(fn)["parms"].get()
    names = [str(n) for n in h.axes[0]]
    return {
        n: float(v) for n, v in zip(names, h.values()) if n != BLIND
    }  # alpha_s never read


t0 = time.time()
core = ScetlibADXsec(
    f"{args.cache}/cache.conf", f"{args.cache}/cache.npz", threads=args.threads
)
print(f"[load] {time.time()-t0:.0f}s", flush=True)
snames = list(core.param_names)
rnames = [adp.rabbit_name(s) for s in snames]
anchor = np.asarray(core.anchor, dtype=np.float64).copy()
ridx = {r: i for i, r in enumerate(rnames)}
bins = np.asarray(core.bins)
print("bins", bins.shape, "unique Y", np.unique(bins[:, 2:4], axis=0).tolist())
print("anchor (NP):", {n: anchor[ridx[n]] for n in NP if n in ridx})


def physical(r, th):
    spec = adp.reparam(r)
    a = anchor[ridx[r]]
    if spec is None:
        return th * (args.pdf_coeff_scale if r.startswith(adp.PDF_PREFIX_OUT) else 1.0)
    kind, c = spec
    if kind == "unit":
        return a + c[0] * th
    if kind == "quad":
        return c[0] + c[1] * th + c[2] * th * th
    if kind == "log":
        return np.exp(c[0] * th)
    raise ValueError(kind)


def vector(theta, which):
    v = anchor.copy()
    for r, th in theta.items():
        if r == BLIND or r not in ridx:
            continue
        if which == "NP" and r not in NP:
            continue
        v[ridx[r]] = physical(r, th)
    assert v[ridx[BLIND]] == anchor[ridx[BLIND]]
    return v


th_fit, th_ref = read_theta(args.fit), read_theta(args.ref)
used = [r for r in th_fit if r in ridx]
print("fit params mapped into the cache vector (alphaS excluded):", len(used), used)
pts = {
    "anchor": anchor.copy(),
    "fitA": vector(th_fit, "NP"),
    "fitB": vector(th_fit, "all"),
    "selfA": vector(th_ref, "NP"),
}
for k in pts:
    print(k, {n: round(float(pts[k][ridx[n]]), 6) for n in NP if n in ridx})

H = args.h
ncall = [0]


def vj(pv):
    ncall[0] += 1
    v, J = core.values_and_jacobian(pv)
    return np.asarray(v, dtype=np.float64), np.asarray(J, dtype=np.float64)


def evaluate(pv, fd_cols):
    v, J = vj(pv)
    res = dict(sigma=v, J={}, fwd={}, bwd={})
    for c in fd_cols:
        i = ridx[c]
        pp, pm = pv.copy(), pv.copy()
        pp[i] += H
        pm[i] -= H
        vp, _ = vj(pp)
        vm, _ = vj(pm)
        res["J"][c] = J[:, i]
        res["fwd"][c] = (vp - v) / H
        res["bwd"][c] = (v - vm) / H
    return res


out = {}
L2of = lambda pv: pv[ridx["lambda2"]] + 6.25 * pv[ridx["delta_lambda2"]]
for k, pv in pts.items():
    t = time.time()
    out[k] = evaluate(pv, TMD_COLS + ["lambda2_nu"])
    out[k]["p"] = pv
    print(
        f"[{k}] {time.time()-t:.0f}s  L2(2.5)={L2of(pv):+.4f}  min sigma {out[k]['sigma'].min():.4g}  n<=0 {(out[k]['sigma']<=0).sum()}",
        flush=True,
    )

L2T = np.round(np.arange(0.05, -0.0501, -0.005), 4)
base = pts["fitB"]
for mode in ["dl2", "l2"]:
    for L2 in L2T:
        pv = base.copy()
        if mode == "dl2":
            pv[ridx["delta_lambda2"]] = (L2 - pv[ridx["lambda2"]]) / 6.25
        else:
            pv[ridx["lambda2"]] = L2 - 6.25 * pv[ridx["delta_lambda2"]]
        t = time.time()
        key = f"scan_{mode}_{L2:+.3f}"
        out[key] = evaluate(pv, ["lambda2", "delta_lambda2"])
        out[key]["p"] = pv
        print(
            f"[{key}] {time.time()-t:.0f}s  min sigma {out[key]['sigma'].min():.4g}  n<=0 {(out[key]['sigma']<=0).sum()}",
            flush=True,
        )

flat = {"bins": bins, "param_names": np.array(rnames), "L2T": L2T}
for k, r in out.items():
    flat[f"{k}__sigma"] = r["sigma"]
    flat[f"{k}__p"] = r["p"]
    for c in r["J"]:
        for s in ("J", "fwd", "bwd"):
            flat[f"{k}__{s}__{c}"] = r[s][c]
# the alpha_s slot of every stored vector is the ANCHOR (asserted above), so saving p is blinding-safe
np.savez(os.path.join(args.outdir, "check2_model_eval.npz"), **flat)
print(f"CHECK2_DONE calls={ncall[0]} total {time.time()-t0:.0f}s")
