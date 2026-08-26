#!/usr/bin/env python3
"""Proof that the PDF CL scaling is in, and that it is normalisation-neutral.

ONE model load. Four things:
  1. the resolved scale comes from theory_utils.pdfMap, not a constant;
  2. _physical / _physical_tf touch the pdfEig slots and NOTHING else;
  3. the reco eigenvector response at theta = +-1 lands on the card's SymAvg
     templates, per eigenvector and in quadrature;
  4. evaluate-at-scale vs scale-the-response, for the curved eigenvectors.
"""
import argparse, os, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
sys.path.insert(0, os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants"))

ap = argparse.ArgumentParser()
ap.add_argument("--datacard", required=True)
ap.add_argument("--cache", required=True)
ap.add_argument("--conf", required=True)
ap.add_argument("--cardhalves", required=True, help="npz from card_convention.py")
ap.add_argument("--threads", type=int, default=32)
ap.add_argument("--out", required=True)
a = ap.parse_args()

from rabbit.inputdata import FitInputData
from wremnants.postprocessing.scetlib_ad import params as adp
from wremnants.postprocessing.scetlib_ad.param_model import SCETlibADParamModel

indata = FitInputData(a.datacard)
# arm B's own parameter set: "all" minus the one identically-null column (D-016).
_cnames = [str(x) for x in np.load(a.cache, allow_pickle=True)["names"]]
_fp = [adp.rabbit_name(n) for n in _cnames]
_fp = [n for n in _fp if n not in adp.DEFAULT_FROZEN and n != "resumTNP_b_qqDS"]
model = SCETlibADParamModel(indata, cache=a.cache, conf=a.conf, gen_level=0,
                            threads=a.threads, fit_params=",".join(_fp),
                            poi_params="alphaS", priors=1, jitCompile="off")
s = model.pdf_coeff_scale
print("\n" + "=" * 78)
print(f"1. RESOLVED SCALE  pdf_coeff_scale = {s:.8f}")
print(f"   theory_utils route: pdf_coeff_scale('CT18ZNNLO', ['alphaS']) = "
      f"{adp.pdf_coeff_scale('CT18ZNNLO', ['alphaS']):.8f}")
print(f"   1/1.645 = {1/1.645:.8f}   agree: {abs(s - 1/1.645) < 1e-12}")
for lha, noi in [("CT18ZNNLO", ["alphaS"]), ("CT18ZNNLO", ["wmass"]),
                 ("NNPDF31_nnlo_hessian_pdfas", ["alphaS"]),
                 ("MSHT20nnlo_as118", ["alphaS"]), ("MSHT20nnlo_as118", ["wmass"]),
                 ("HERAPDF20_NNLO_EIG", ["alphaS"])]:
    print(f"   generality check  {lha:<28} noi={str(noi):<11} -> "
          f"{adp.pdf_coeff_scale(lha, noi):.6f}")

names = list(model._param_order)
print("\n" + "=" * 78)
print("2. WHAT THE MAP TOUCHES")
rng = np.random.default_rng(7)
th = rng.normal(size=len(names))
ph = model._physical(th)
import tensorflow as tf
ph_tf = np.asarray(model._physical_tf(tf.constant(th, tf.float64)).numpy())
print(f"   _physical vs _physical_tf: max|diff| = {np.abs(ph - ph_tf).max():.3e}")
npdf = nother = 0
bad = []
for i, n in enumerate(names):
    if n.startswith("pdfEig"):
        npdf += 1
        if abs(ph[i] - s * th[i]) > 1e-14 * max(1, abs(th[i])):
            bad.append((n, th[i], ph[i], s * th[i]))
    else:
        nother += 1
        if adp.reparam(n) is None and abs(ph[i] - th[i]) > 0:
            bad.append((n, th[i], ph[i], th[i]))
print(f"   {npdf} pdfEig slots map theta -> {s:.5f}*theta; "
      f"{nother} others untouched (reparam names excluded, they were already "
      f"nonlinear). Violations: {len(bad)} {bad[:3]}")
print(f"   _rp_scale != 1 on exactly: {sorted(set(n for n, f in zip(names, model._rp_scale != 1) if f))[:3]} ... "
      f"({int((model._rp_scale != 1).sum())} of {len(names)})")
print(f"   anchor round trip at theta=0 passed at construction (else __init__ raises)")

# --- 3/4: reco response, from the SCETlib vector directly (bypasses _physical,
# so the two routes are independent) ------------------------------------------
R = np.asarray(model.R.numpy(), float)
sr0 = np.asarray(model.sigma_reco_central.numpy(), float)
core = model.core; cn = list(core.param_names); anchor = np.asarray(core.anchor, float)
neig = sum(1 for n in cn if n.startswith("pdf_eig"))
nb = sr0.size

def reco_ln(idx, c):
    p = anchor.copy(); p[cn.index(f"pdf_eig{idx}")] = c
    vals, _ = core.values_and_jacobian(p)
    return np.log((R @ model._fold(np.asarray(vals, float))) / sr0)

Up = np.zeros((nb, neig)); Dn = np.zeros((nb, neig))
Ups = np.zeros((nb, neig)); Dns = np.zeros((nb, neig))
for i in range(neig):
    Up[:, i] = reco_ln(i, +1.0); Dn[:, i] = reco_ln(i, -1.0)
    Ups[:, i] = reco_ln(i, +s);  Dns[:, i] = reco_ln(i, -s)
    print(f"   eig {i:2d} done", flush=True)
D = 0.5 * (Up - Dn); A = 0.5 * (Up + Dn)          # raw member halves, c = +-1
Ds = 0.5 * (Ups - Dns); As = 0.5 * (Ups + Dns)    # at the 68% CL point

z = np.load(a.cardhalves)
CA, CD = z["CA"], z["CD"]                          # card SymAvg / SymDiff logk
w = np.asarray(indata.data_obs)[:nb]
wm = lambda x: float((x * w).sum() / w.sum())
q = lambda M: np.sqrt((M ** 2).sum(1))

print("\n" + "=" * 78)
print("3. PREFIT PDF BAND, card templates vs model, per reco bin (relative)")
rows = [
  ("card, all 58 templates (SymAvg + SymDiff)",      q(np.concatenate([CA, CD], 1))),
  ("card, the 29 SymAvg only  (= s * D, linear)",    q(CA)),
  ("card, the 29 SymDiff only (= s*sqrt3 * A, quad)",q(CD)),
  ("model BEFORE, sigma=1 at c=+-1 (linearised)",    q(D)),
  ("model AFTER,  sigma=1 at c=+-s (linearised)",    q(Ds)),
  ("model AFTER,  s * D (response-scale variant)",   s * q(D)),
]
print(f"   {'quantity':<48} {'wmean':>12} {'max':>12}")
for n, x in rows:
    print(f"   {n:<48} {wm(x):>12.5e} {x.max():>12.5e}")
lin_card, lin_model = q(CA), q(Ds)
r = lin_card / np.where(lin_model > 0, lin_model, np.nan)
print(f"\n   LINEAR (1 sigma) PDF response, card SymAvg / model-after:")
print(f"     wmean {wm(np.nan_to_num(r)):.5f}   median {np.nanmedian(r):.5f}   "
      f"min {np.nanmin(r):.5f}   max {np.nanmax(r):.5f}")
tot_card = q(np.concatenate([CA, CD], 1))
rt = tot_card / np.where(lin_model > 0, lin_model, np.nan)
print(f"   TOTAL card band / model-after linear band: wmean {wm(np.nan_to_num(rt)):.5f} "
      f"(the residual is the SymDiff surrogate, see 4)")
rb = tot_card / np.where(q(D) > 0, q(D), np.nan)
print(f"   TOTAL card band / model-BEFORE:            wmean {wm(np.nan_to_num(rb)):.5f}"
      f"  <- the reported 0.853")
# model's own predictive sd including its genuine quadratic term, theta ~ N(0,1)
sd_full = np.sqrt((Ds ** 2 + 2 * As ** 2).sum(1))
print(f"   model-after full predictive sd sqrt(D_s^2 + 2 A_s^2): wmean {wm(sd_full):.5e}"
      f"   card/this = {wm(tot_card)/wm(sd_full):.5f}")

print("\n" + "=" * 78)
print("4. PER-EIGENVECTOR: card SymAvg vs model linear response at c = +-s")
print(f"   {'e':>3} {'|CA|':>11} {'|s*D|':>11} {'|D_s|':>11} {'CA/D_s':>9} "
      f"{'|A|/|D|':>8} {'evalS/scaleS':>13} {'quad shift':>11}")
ratios = []
for i in range(neig):
    nca, nsd, nds = np.linalg.norm(CA[:, i]), s * np.linalg.norm(D[:, i]), np.linalg.norm(Ds[:, i])
    ad = np.linalg.norm(A[:, i]) / np.linalg.norm(D[:, i])
    # what theta=+1 actually predicts, two ways
    ev = Ups[:, i]                 # evaluate at c = s          (implemented)
    sc = s * Up[:, i]              # scale the c = 1 response    (template convention)
    rel = np.linalg.norm(ev - sc) / max(np.linalg.norm(ev), 1e-300)
    ratios.append(nca / nds)
    print(f"   {i:>3} {nca:>11.4e} {nsd:>11.4e} {nds:>11.4e} {nca/nds:>9.4f} "
          f"{ad:>8.3f} {np.linalg.norm(ev)/max(np.linalg.norm(sc),1e-300):>13.4f} "
          f"{rel:>11.4f}")
ratios = np.array(ratios)
print(f"\n   card SymAvg / model : mean {ratios.mean():.5f} min {ratios.min():.5f} "
      f"max {ratios.max():.5f} std {ratios.std():.5f}")
ev1 = Ups; sc1 = s * Up
relall = np.linalg.norm(ev1 - sc1, axis=0) / np.linalg.norm(ev1, axis=0)
print(f"   evaluate-at-s vs scale-response, ||delta||/||resp|| per eigenvector: "
      f"median {np.median(relall):.4f}  e0 {relall[0]:.4f}  e3 {relall[3]:.4f}  "
      f"max {relall.max():.4f}")
np.savez(a.out, Up=Up, Dn=Dn, Ups=Ups, Dns=Dns, w=w, s=s)
print("\nsaved", a.out)
