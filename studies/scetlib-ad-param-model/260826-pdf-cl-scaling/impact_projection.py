#!/usr/bin/env python3
"""What the CL scaling does to the PDF impact on alpha_s, and the band figure."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

T = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260826-pdf-cl-scaling"
m = np.load(f"{T}/model_responses.npz"); c = np.load(f"{T}/card_halves.npz")
s = float(m["s"]); w = m["w"]
Up, Dn, Ups, Dns = m["Up"], m["Dn"], m["Ups"], m["Dns"]
D, A = 0.5*(Up-Dn), 0.5*(Up+Dn)
Ds, As = 0.5*(Ups-Dns), 0.5*(Ups+Dns)
CA, CD = c["CA"], c["CD"]
q = lambda M: np.sqrt((M**2).sum(1)); wm = lambda x: float((x*w).sum()/w.sum())

bands = {
    "card total (58)":      q(np.concatenate([CA, CD], 1)),
    "card SymAvg (linear)": q(CA),
    "card SymDiff (quad)":  q(CD),
    "model before":         q(D),
    "model after (linear)": q(Ds),
    "model after (full sd)":np.sqrt((Ds**2 + 2*As**2).sum(1)),
}
print("PREFIT PDF BAND, yield-weighted mean over the 780 reco bins")
for k, v in bands.items():
    print(f"  {k:<24} {wm(v):.5e}")
print()
print(f"  card SymAvg / model after   = {wm(bands['card SymAvg (linear)'])/wm(bands['model after (linear)']):.5f}")
print(f"  card total  / model after   = {wm(bands['card total (58)'])/wm(bands['model after (linear)']):.5f}")
print(f"  card total  / model before  = {wm(bands['card total (58)'])/wm(bands['model before']):.5f}")
print(f"  model after full/linear     = {wm(bands['model after (full sd)'])/wm(bands['model after (linear)']):.5f}"
      f"   (curvature the Hessian does not see)")
print(f"  card total / model full sd  = {wm(bands['card total (58)'])/wm(bands['model after (full sd)']):.5f}"
      f"   (the card's OVER-inflation of that same curvature)")
print(f"  card quad amplitude / physical s^2 A : sqrt(3)/s = {np.sqrt(3)/s:.4f}")

# --- impacts -----------------------------------------------------------------
sA_tot, sA_pdf = 1.49056e-3, 1.08338e-3      # arm A, PDF as templates
sB_tot, sB_pdf = 1.62004e-3, 1.25558e-3      # arm B, PDF in model, NO CL scale
band_ratio = wm(bands["model before"]) / wm(bands["card total (58)"])
print("\nGROUPED IMPACT on alpha_s (Asimov, 2D ptll-yll, real-data card)")
print(f"  arm A templates   sigma {sA_tot:.5e}  pdfCT18ZNoAlphaS {sA_pdf:.5e}")
print(f"  arm B model (raw) sigma {sB_tot:.5e}  pdfEig           {sB_pdf:.5e}")
print(f"  impact ratio B/A {sB_pdf/sA_pdf:.4f}   prefit band ratio B/A {band_ratio:.4f}"
      f"   -> impact tracks the band to {abs(sB_pdf/sA_pdf/band_ratio-1)*100:.2f}%")
nonpdfA = np.sqrt(sA_tot**2 - sA_pdf**2); nonpdfB = np.sqrt(sB_tot**2 - sB_pdf**2)
print(f"  non-PDF part in quadrature: A {nonpdfA:.5e}  B {nonpdfB:.5e}  "
      f"B/A {nonpdfB/nonpdfA:.4f}  (the arms differ ONLY in the PDF treatment)")
k = wm(bands["model after (linear)"]) / wm(bands["model before"])
pred_pdf = sB_pdf * k
pred_tot = np.sqrt(nonpdfB**2 + pred_pdf**2)
print(f"\n  PROJECTION after the CL scale (response shrinks by {k:.5f}):")
print(f"    pdfEig impact  {pred_pdf:.5e}   ({pred_pdf/sA_pdf:.4f} x the template arm)")
print(f"    sigma(alphaS)  {pred_tot:.5e}   ({pred_tot/sA_tot:.4f} x the template arm,"
      f" {pred_tot/sB_tot:.4f} x arm B as run)")
print("    PROJECTION ONLY -- linear in the band, validated to 0.06% on the A/B pair above.")

# --- figure ------------------------------------------------------------------
edges = np.array([0,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,
                  11,11.5,12,13,14,15,16,17,18,19,20,22,24,26,28,30,33,37,44.])
ctr = 0.5*(edges[1:]+edges[:-1])
prof = lambda b: (b.reshape(39,20)*w.reshape(39,20)).sum(1)/w.reshape(39,20).sum(1)
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))
sty = [("card total (58)", "k", "-", 2.0), ("card SymAvg (linear)", "C3", "--", 1.6),
       ("card SymDiff (quad)", "C1", ":", 1.6), ("model before", "C0", "-.", 1.6),
       ("model after (linear)", "C2", "-", 2.0)]
for k_, col, ls, lw in sty:
    ax[0].plot(ctr, 100*prof(bands[k_]), color=col, ls=ls, lw=lw, label=k_)
ax[0].set_xlabel(r"$p_T^{\ell\ell}$ [GeV]"); ax[0].set_ylabel("prefit PDF band [%]")
ax[0].set_title("PDF band, yield-averaged over $|y_{\\ell\\ell}|$"); ax[0].legend(fontsize=7.5)
ax[0].grid(alpha=.3)
r_after = prof(bands["card SymAvg (linear)"])/prof(bands["model after (linear)"])
r_before = prof(bands["card total (58)"])/prof(bands["model before"])
r_tot = prof(bands["card total (58)"])/prof(bands["model after (linear)"])
ax[1].axhline(1.0, color="k", lw=.8)
ax[1].plot(ctr, r_before, "C0-.", lw=1.6, label=f"card total / model BEFORE ({wm(bands['card total (58)'])/wm(bands['model before']):.3f})")
ax[1].plot(ctr, r_tot, "C4-", lw=1.4, label=f"card total / model AFTER ({wm(bands['card total (58)'])/wm(bands['model after (linear)']):.3f}); the $\\sqrt{{3}}$ surrogate")
ax[1].plot(ctr, r_after, "C2-", lw=2.2, label=f"card SymAvg / model AFTER ({wm(bands['card SymAvg (linear)'])/wm(bands['model after (linear)']):.3f})  <- like for like")
ax[1].set_xlabel(r"$p_T^{\ell\ell}$ [GeV]"); ax[1].set_ylabel("card / model")
ax[1].set_title("normalisation neutrality of the swap"); ax[1].legend(fontsize=7.5)
ax[1].grid(alpha=.3); ax[1].set_ylim(0.5, 1.6)
fig.tight_layout(); fig.savefig(f"{T}/pdf_cl_scaling_band.png", dpi=140)
print("\nwrote", f"{T}/pdf_cl_scaling_band.png")
