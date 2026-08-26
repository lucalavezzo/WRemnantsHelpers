#!/usr/bin/env python3
"""PDF-eigenvector CONVENTION and DEGENERACY diagnostics for a 62-member cache.

`validate_variations.py` answers "does the model reproduce the template", which
is the deliverable. This answers the two questions that a max|dev| number
cannot, and that must be settled before that number is read as agreement:

  1. CONVENTION.  CT18Z is a Hessian set at 90% CL. If the templates carry raw
     eigenvector members while the model's ``pdf_eigN`` were normalised
     differently (68% CL, a factor 1/1.645, per-member vs per-pair), the model
     response would be the template's raised to a CONSTANT power -- a clean
     scale factor in log, flat over bins and eigenvectors. So regress

         ln r_model  =  s * ln r_ref            (least squares through 0)

     per direction. s == 1 for all 58 is the statement "same convention on both
     sides". A sign-convention difference on the down member instead shows as
     s == -1 against its own template and s == +1 against its PARTNER, so both
     slopes are reported.

  2. DEGENERACY.  The backend refuses a parameter whose Jacobian column is
     identically zero (that is how ``tnp_b_qqDS`` was caught for the Z). A
     NEAR-degenerate eigenvector is invisible to that guard and would make a
     53-parameter fit ill-conditioned. Reported as per-column norms, the worst
     off-diagonal cosine between eigenvector columns, and the singular-value
     spectrum of the eigenvector block and of the full Jacobian.

Also PROVES the arms are separated (the ``values_and_jacobian`` memoisation
trap): every returned value array is hashed and the count of distinct hashes is
printed. A memoised collision would return the same array twice.

Writes an .npz with every response so the tables and plots can be remade
without paying the ~10 min / ~60 GB cache load again.
"""

import argparse
import hashlib
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad"
sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants")
sys.path.insert(0, _SCRIPTS)

import validate_variations as vv  # noqa: E402  -- reuse its readers, do not reimplement

from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--cache", required=True)
ap.add_argument("--conf", required=True)
ap.add_argument("--corr-pdfvars", required=True)
ap.add_argument("--threads", type=int, default=64)
ap.add_argument("--out", required=True, help="output .npz")
ap.add_argument(
    "--ln-floor",
    type=float,
    default=1e-4,
    help="bins with |ln r_ref| below this are excluded from the slope fit; "
    "they carry no information about a scale factor and would only add noise",
)
a = ap.parse_args()

core = ScetlibADXsec(a.conf, a.cache, threads=a.threads)
names = list(core.param_names)
print(f"cache: {core.n_bins} bins, {core.n_params} params", flush=True)

b = core.bins
yl = np.unique(np.round(b[:, 2:4], 12), axis=0)
tl = np.unique(np.round(b[:, 4:6], 12), axis=0)
yl, tl = yl[np.argsort(yl[:, 0])], tl[np.argsort(tl[:, 0])]
Ye = np.concatenate([yl[:, 0], yl[-1:, 1]])
Te = np.concatenate([tl[:, 0], tl[-1:, 1]])
nT, nY = Te.size - 1, Ye.size - 1
print(f"model grid: |Y| {nY} bins [{Ye[0]:g},{Ye[-1]:g}], qT {nT} bins "
      f"[{Te[0]:g},{Te[-1]:g}]", flush=True)

fold = core.fold_for([("ptVGen", Te), ("absYVGen", Ye)], b[0, 0], b[0, 1])
print("fold:", fold.describe(), flush=True)

anchor = core.anchor.copy()
_hashes = {}


def model_on_grid(overrides, tag):
    p = anchor.copy()
    for k, val in overrides.items():
        p[names.index(k)] = val
    vals, _ = core.values_and_jacobian(p)
    vals = np.asarray(vals, float)
    _hashes[tag] = hashlib.md5(vals.tobytes()).hexdigest()
    return fold(vals).reshape(nT, nY).T  # -> (|Y|, qT)


# ---- Jacobian at the anchor: the degeneracy question
val0, jac = core.values_and_jacobian(anchor)
val0 = np.asarray(val0, float)
jac = np.asarray(jac, float)
_hashes["anchor"] = hashlib.md5(val0.tobytes()).hexdigest()
s_cen = fold(val0).reshape(nT, nY).T

# ---- reference
labels, cen_lab, ref_on_grid = vv.make_reference_like = None, None, None
h = vv.load_corr(a.corr_pdfvars)
ax = {x.name: x for x in h.axes}
labels = [str(x) for x in ax["vars"]]
vals = np.asarray(h.values(flow=False))
dims = [x.name for x in h.axes]
iQ, ich = dims.index("Q"), dims.index("charge")
vals = np.squeeze(vals, axis=(iQ, ich))
order = [d for d in dims if d not in ("Q", "charge")]
vals = np.moveaxis(
    vals, [order.index("absY"), order.index("qT"), order.index("vars")], [0, 1, 2]
)
MY = vv.merge_matrix(ax["absY"].edges, Ye, "absY")
MT = vv.merge_matrix(ax["qT"].edges, Te, "qT")


def ref_grid(label):
    return MY @ vals[:, :, labels.index(label)] @ MT.T


cen_lab = vv.central_label(labels)
r_cen = ref_grid(cen_lab)
print(f"reference central label: {cen_lab}; {len(labels)} members", flush=True)

n_eig = int(np.load(a.cache)["n_eig"]) if False else sum(
    1 for n in names if n.startswith("pdf_eig")
)
print(f"model carries {n_eig} pdf_eig parameters", flush=True)

qT_mid = 0.5 * (Te[:-1] + Te[1:])
mask_qt1 = qT_mid > 1.0  # drop the known qT [0,1] nonsingular-cutoff convention bin

R_model, R_ref, tags = {}, {}, []
for i in range(n_eig):
    for side, sgn in (("up", +1.0), ("dn", -1.0)):
        lab = f"pdf{2 * i + 1 + (0 if side == 'up' else 1)}"
        tag = f"eig{i}{side}"
        tags.append(tag)
        R_model[tag] = model_on_grid({f"pdf_eig{i}": sgn}, tag) / s_cen
        R_ref[tag] = ref_grid(lab) / r_cen
        print(f"  {tag:<10} <- model pdf_eig{i}={sgn:+g}  vs template {lab}",
              flush=True)

nd = len(set(_hashes.values()))
print(f"\nARM SEPARATION: {len(_hashes)} model evaluations -> {nd} distinct "
      f"value arrays  -> {'OK, arms separated' if nd == len(_hashes) else 'COLLISION'}",
      flush=True)

# ---- convention: least-squares slope in log
print("\nCONVENTION: ln r_model = s * ln r_ref, LS through the origin")
print(f"{'direction':<12}{'s (qT>1)':>10}{'s (all qT)':>12}{'s vs partner':>14}"
      f"{'nbin':>6}{'max|r_m/r_r-1| qT>1':>22}{'  (all qT)':>12}")
rows = []
for i in range(n_eig):
    for side in ("up", "dn"):
        tag = f"eig{i}{side}"
        other = f"eig{i}{'dn' if side == 'up' else 'up'}"
        lm, lr = np.log(R_model[tag]), np.log(R_ref[tag])
        lp = np.log(R_ref[other])
        ok = np.isfinite(lm) & np.isfinite(lr) & (np.abs(lr) > a.ln_floor)
        okq = ok & mask_qt1[None, :]

        def slope(m, num, den):
            return float(np.sum(num[m] * den[m]) / np.sum(den[m] ** 2))

        s_q = slope(okq, lm, lr) if okq.sum() else np.nan
        s_a = slope(ok, lm, lr) if ok.sum() else np.nan
        okp = np.isfinite(lm) & np.isfinite(lp) & (np.abs(lp) > a.ln_floor) & mask_qt1[None, :]
        s_p = slope(okp, lm, lp) if okp.sum() else np.nan
        d = np.abs(R_model[tag] / R_ref[tag] - 1.0)
        dq = float(np.nanmax(np.where(mask_qt1[None, :], d, np.nan)))
        da = float(np.nanmax(d))
        rows.append((tag, s_q, s_a, s_p, int(okq.sum()), dq, da))
        print(f"{tag:<12}{s_q:>10.5f}{s_a:>12.5f}{s_p:>14.5f}{int(okq.sum()):>6}"
              f"{dq:>22.2e}{da:>12.2e}")

sq = np.array([r[1] for r in rows])
print(f"\nslope over the {len(rows)} directions (qT>1): mean {sq.mean():.6f}, "
      f"min {sq.min():.6f}, max {sq.max():.6f}, "
      f"max|s-1| {np.max(np.abs(sq - 1)):.2e}")
print("  s == 1 -> the template members and the model's pdf_eigN are the SAME "
      "convention (raw Hessian member, per-pair, c_e = +-1).")
print(f"  1/1.645 = {1/1.645:.5f}, 1.645, -1 are the signatures this test would "
      "have shown for a 90/68% CL or sign mismatch.")

# ---- finite-difference step-size scan on the zero-anchored eigenvectors.
# backend_check uses h = 1e-4 * max(|anchor_i|, 1e-3), i.e. h = 1e-7 for every
# pdf_eigN, which is anchored at 0. A correct analytic gradient shows the classic
# V: round-off ~ eps*sigma/h falling as h grows, truncation ~ h^2 rising. A wrong
# gradient is FLAT. This is the experiment that separates the two.
print("\nFD STEP-SIZE SCAN (|analytic - FD| / |FD| on d(sum sigma)/dp)")
steps = [1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
hdr = f"{'parameter':<18}{'analytic':>15}" + "".join(f"{('h=%g' % h):>11}" for h in steps)
print(hdr)
for nm in ("pdf_eig0", "pdf_eig5", "pdf_eig28", "alphas"):
    i = names.index(nm)
    an = float(jac[:, i].sum())
    row = f"{nm:<18}{an:>15.8g}"
    for hh in steps:
        pp, pm = anchor.copy(), anchor.copy()
        pp[i] += hh
        pm[i] -= hh
        fd = (np.asarray(core.values_and_jacobian(pp)[0]).sum()
              - np.asarray(core.values_and_jacobian(pm)[0]).sum()) / (2 * hh)
        row += f"{abs(an - fd) / max(abs(fd), 1e-300):>11.2e}"
    print(row, flush=True)
print(f"  sum(sigma) at the anchor = {val0.sum():.8g}; the double-precision "
      f"round-off floor on a central difference is ~eps*sum(sigma)/h.")

# ---- degeneracy
ie = [k for k, n in enumerate(names) if n.startswith("pdf_eig")]
Je = jac[:, ie]
nrm = np.linalg.norm(Je, axis=0)
nrm_all = np.linalg.norm(jac, axis=0)
print("\nDEGENERACY of the eigenvector directions (Jacobian columns at the anchor)")
zero_cols = [names[k] for k in range(len(names)) if nrm_all[k] == 0.0]
print(f"  exactly-zero columns among all {len(names)}: {zero_cols or 'none'}")
o = np.argsort(nrm)
print(f"  eigenvector column norms: max {nrm.max():.4g} (pdf_eig{o[-1]}), "
      f"min {nrm.min():.4g} (pdf_eig{o[0]}), ratio {nrm.min()/nrm.max():.3e}")
print("  weakest five: " + ", ".join(f"pdf_eig{k}={nrm[k]:.3g}" for k in o[:5]))
U = Je / nrm
C = U.T @ U
np.fill_diagonal(C, 0.0)
k = np.unravel_index(np.argmax(np.abs(C)), C.shape)
print(f"  worst |cos| between two eigenvector columns: {np.abs(C).max():.4f} "
      f"(pdf_eig{k[0]}, pdf_eig{k[1]})")
sv = np.linalg.svd(U, compute_uv=False)
print(f"  singular values of the NORMALISED eigenvector block: max {sv[0]:.4g}, "
      f"min {sv[-1]:.4g}, cond {sv[0]/sv[-1]:.4g}")
U_all = jac / np.where(nrm_all == 0, 1, nrm_all)
keep = nrm_all > 0
sva = np.linalg.svd(U_all[:, keep], compute_uv=False)
print(f"  full Jacobian ({int(keep.sum())} non-null columns, normalised): "
      f"cond {sva[0]/sva[-1]:.4g}, smallest sv {sva[-1]:.3g}")

np.savez_compressed(
    a.out,
    Te=Te, Ye=Ye, s_cen=s_cen, r_cen=r_cen, val0=val0,
    jac=jac, names=np.array(names), anchor=anchor,
    eig_cols=np.array(ie),
    tags=np.array(tags),
    R_model=np.stack([R_model[t] for t in tags]),
    R_ref=np.stack([R_ref[t] for t in tags]),
    slope_qt1=sq, slope_all=np.array([r[2] for r in rows]),
    slope_partner=np.array([r[3] for r in rows]),
    dev_qt1=np.array([r[5] for r in rows]), dev_all=np.array([r[6] for r in rows]),
)
print(f"\nwrote {a.out}")
