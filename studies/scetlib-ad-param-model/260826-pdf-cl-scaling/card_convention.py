#!/usr/bin/env python3
"""What factor does the CARD actually apply to the CT18Z PDF templates?

Measured from the card's own logk against the histmaker reco pdfvars hist that
setupRabbit built the templates from.  Convention under test (rabbit
tensorwriter.py:371-386, with logkdown = -ln(down/nom)):

    SymAvg  logk = scale * 0.5*(ln u - ln d)            = scale * D   (ANTIsym, linear)
    SymDiff logk = scale * 0.5*sqrt(3)*(ln u + ln d)    = scale*r3* A (sym, quadratic)

i.e. the name "Avg" carries the ANTIsymmetric half and "Diff" the symmetric one.
"""
import argparse
import numpy as np, h5py
from rabbit.inputdata import FitInputData
from wums import ioutils as wums_io

ap = argparse.ArgumentParser()
ap.add_argument("--card", required=True)
ap.add_argument("--histmaker", required=True)
ap.add_argument("--sample", default="Zmumu_2016PostVFP")
ap.add_argument("--proc", default="Zmumu")
ap.add_argument("--hist", default="nominal_ptll_yll_scetlib_dyturbo_LatticeNPLambda4Bugfix_"
                                 "FranksValsVars_CT18Z_N3p0LL_N2LO_pdfvars_Corr")
ap.add_argument("--npz", default=None)
a = ap.parse_args()

d = FitInputData(a.card)
dec = lambda x: x.decode() if isinstance(x, bytes) else str(x)
systs = [dec(s) for s in d.systs]; procs = [dec(p) for p in d.procs]
ip = procs.index(a.proc); nb = d.nbins
logk = np.asarray(d.logk)
logk_s = logk[:, ip, 0, :] if logk.ndim == 4 else logk[:, ip, :]
logk_s = logk_s[:nb]
print(f"card {a.card}\n  logk {logk.shape}  symmetric_tensor {getattr(d,'symmetric_tensor',None)}  nbins {nb}")

# --- sanity: lumi must come back flat at the declared 1.2%
if "lumi" in systs:
    l = logk_s[:, systs.index("lumi")]
    print(f"  SANITY lumi: exp(logk)-1 = {np.exp(l).mean()-1:.6f} +- {np.exp(l).std():.3e}")

with h5py.File(a.histmaker, "r") as f:
    s = wums_io.pickle_load_h5py(f[a.sample]); h = s["output"][a.hist]
    h = h.get() if hasattr(h, "get") else h
labels = [str(x) for x in h.axes["vars"]]
names = [ax.name for ax in h.axes]
vals = np.moveaxis(np.asarray(h.values(flow=False), float), names.index("vars"), -1)[:39, :20, :]
flat = vals.reshape(-1, vals.shape[-1]); assert flat.shape[0] == nb
cen = flat[:, labels.index("pdf0")]; ok = cen > 0
ln = lambda lbl: np.log(flat[:, labels.index(lbl)] / cen, where=ok, out=np.zeros(nb))

D = np.zeros((nb, 29)); A = np.zeros((nb, 29))
CA = np.zeros((nb, 29)); CD = np.zeros((nb, 29))
for i in range(29):
    u, v = ln(f"pdf{2*i+1}"), ln(f"pdf{2*i+2}")
    D[:, i] = 0.5 * (u - v)                 # antisymmetric / linear derivative
    A[:, i] = 0.5 * (u + v)                 # symmetric / quadratic
    CA[:, i] = logk_s[:, systs.index(f"pdf{i+1}CT18ZSymAvg")]
    CD[:, i] = logk_s[:, systs.index(f"pdf{i+1}CT18ZSymDiff")]

print(f"\nIS SymDiff ZERO?  max|SymDiff logk| over all 29 x {nb} bins = {np.abs(CD).max():.6e}")
print(f"                  max|SymAvg  logk|                        = {np.abs(CA).max():.6e}")
print(f"  n eigenvectors with max|SymDiff| < 1e-12 : {(np.abs(CD).max(0) < 1e-12).sum()} of 29")

def slope(y, x):
    m = ok & (np.abs(x) > 1e-5 * np.abs(x).max())
    if m.sum() < 20: return np.nan, np.nan, int(m.sum())
    return (float((x[m]*y[m]).sum()/(x[m]**2).sum()),
            float(np.corrcoef(x[m], y[m])[0, 1]), int(m.sum()))

print("\nPER-EIGENVECTOR: card logk regressed on the histmaker halves")
print("  hypothesis  SymAvg/D = 1/1.645 = 0.60790 ;  SymDiff/A = sqrt(3)/1.645 = 1.05292")
print(f"  {'e':>3} {'SymAvg/D':>10} {'r':>7} {'SymDiff/A':>10} {'r':>7} {'|A|/|D|':>8} "
      f"{'SymAvg/A':>10} {'SymDiff/D':>10}")
sA, sD = [], []
for i in range(29):
    a1, r1, _ = slope(CA[:, i], D[:, i]); a2, r2, _ = slope(CD[:, i], A[:, i])
    x1, _, _ = slope(CA[:, i], A[:, i]);  x2, _, _ = slope(CD[:, i], D[:, i])
    ad = np.linalg.norm(A[:, i]) / np.linalg.norm(D[:, i])
    sA.append(a1); sD.append(a2)
    print(f"  {i:>3} {a1:>10.5f} {r1:>7.4f} {a2:>10.5f} {r2:>7.4f} {ad:>8.3f} {x1:>10.5f} {x2:>10.5f}")
sA, sD = np.array(sA), np.array(sD)
print(f"\n  SymAvg/D : mean {sA.mean():.6f}  min {sA.min():.6f}  max {sA.max():.6f}  std {sA.std():.2e}"
      f"   -> /(1/1.645) = {sA.mean()*1.645:.6f}")
print(f"  SymDiff/A: mean {sD.mean():.6f}  min {sD.min():.6f}  max {sD.max():.6f}  std {sD.std():.2e}"
      f"   -> /(sqrt3/1.645) = {sD.mean()*1.645/np.sqrt(3):.6f}")

# --- bin-level uniformity of the single global factor
ok2 = ok[:, None]
m = ok2 & (np.abs(D) > 1e-5 * np.abs(D).max())
rat = np.where(m, CA / np.where(D == 0, np.nan, D), np.nan)
print(f"\n  BIN-LEVEL SymAvg/D over {int(m.sum())} (bin,eig) cells: "
      f"median {np.nanmedian(rat):.6f}  1% {np.nanpercentile(rat,1):.6f}  99% {np.nanpercentile(rat,99):.6f}")
m2 = ok2 & (np.abs(A) > 1e-5 * np.abs(A).max())
rat2 = np.where(m2, CD / np.where(A == 0, np.nan, A), np.nan)
print(f"  BIN-LEVEL SymDiff/A over {int(m2.sum())} cells: "
      f"median {np.nanmedian(rat2):.6f}  1% {np.nanpercentile(rat2,1):.6f}  99% {np.nanpercentile(rat2,99):.6f}")

# --- the band
w = np.asarray(d.data_obs)[:nb]; wm = lambda x: float((x*w).sum()/w.sum())
band_card = np.sqrt(CA**2 + CD**2).sum(axis=1) * 0 + np.sqrt((CA**2 + CD**2).sum(axis=1))
s = 1/1.645
pred_correct = s * np.sqrt((D**2 + 3*A**2).sum(1))
pred_swapped = s * np.sqrt((A**2 + 3*D**2).sum(1))
lin = np.sqrt((D**2).sum(1))
print("\nPREFIT PDF BAND per reco bin (relative)")
for nm, x in [("card logk quadrature, all 58", band_card),
              ("PREDICTED s*sqrt(D^2+3A^2)  [Avg=D, Diff=sqrt3*A]", pred_correct),
              ("PREDICTED s*sqrt(A^2+3D^2)  [the swapped assignment]", pred_swapped),
              ("model proxy, sigma=1, linearised (=|D|)", lin)]:
    print(f"  {nm:<52} wmean {wm(x):.5e}  max {x.max():.5e}")
print(f"\n  card / pred_correct : wmean {wm(band_card)/wm(pred_correct):.5f}  "
      f"per-bin median {np.nanmedian(band_card/pred_correct):.5f}  "
      f"min {np.nanmin(band_card/pred_correct):.5f} max {np.nanmax(band_card/pred_correct):.5f}")
print(f"  card / pred_swapped : wmean {wm(band_card)/wm(pred_swapped):.5f}")
r = band_card/np.where(lin > 0, lin, np.nan)
print(f"  card / linearised model proxy : wmean {wm(np.nan_to_num(r)):.5f} "
      f"median {np.nanmedian(r):.5f} min {np.nanmin(r):.5f} max {np.nanmax(r):.5f}")
asym = np.sqrt((A**2).sum(1))/np.sqrt((D**2).sum(1))
print(f"  ||A||/||D||: wmean {wm(asym):.4f}  min {asym.min():.4f} max {asym.max():.4f}")
print(f"  closed form s*sqrt(1+3*(|A|/|D|)^2) at wmean |A|/|D| = "
      f"{s*np.sqrt(1+3*wm(asym)**2):.5f}   (vs measured card/model {wm(np.nan_to_num(r)):.5f})")
if a.npz:
    np.savez(a.npz, D=D, A=A, CA=CA, CD=CD, w=w, ok=ok)
    print("saved", a.npz)
