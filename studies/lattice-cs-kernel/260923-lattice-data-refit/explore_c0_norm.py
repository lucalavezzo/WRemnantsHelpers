"""sigma(c0) and B_NP diagnostics for the (c0,k1) fit (paper: c0=0.032(12), k1=0.22(8), chi2/dof=0.39).

History: on 2026-09-23 this script "found" a factor 2 in the c0 normalization. That was an artefact
of the d_n index bug in cs_fit.py (fixed 2026-09-24); with the fix c0 reproduces literally. Only the
sigmas remain 2x (c0) and 1.2x (k1) smaller than quoted. This script checks what could inflate them.
"""

import numpy as np
import cs_fit as M

ens, D_ = M.load()
b, y, a, cov = D_["b"], D_["y"], D_["a"], D_["cov"]
for mode in ["numeric", "paper"]:
    r = M.fit(y, cov, b, a, ["c0", "k1"], mode=mode)
    print(mode, "chi2=%.3f" % r["chi2"], M.fmt(r))

print("\nB_NP profile scan, (c0,k1), full cov:")
for mode in ["numeric", "paper"]:
    for B in [1.0, 1.25, 1.5, 1.75, 2.0, 2.2, 2.4, 2.5]:
        r = M.fit(y, cov, b, a, ["c0", "k1"], BNP=B, mode=mode)
        print(f"  {mode:7s} B_NP={B:5.2f} GeV^-1 chi2={r['chi2']:.3f}  {M.fmt(r)}")

print("\nWhat would give sigma(c0)=0.012, sigma(k1)=0.08 ?")
r = M.fit(y, cov, b, a, ["c0", "k1"])
print("  ours:", M.fmt(r))
print("  cov x4 (errors x2):", M.fmt(M.fit(y, 4 * cov, b, a, ["c0", "k1"])))
print(
    "  sigma scaled by sqrt(chi2/ndf) (PDG, would SHRINK):",
    np.sqrt(r["chi2"] / r["ndf"]),
)
# c0 with B_NP profiled (quadrature of B_NP-induced spread) over B in [1.5,2.5]
cs = [
    M.fit(y, cov, b, a, ["c0", "k1"], BNP=B)["theta"]["c0"]
    for B in np.linspace(1.5, 2.5, 11)
]
print("  c0 spread for B_NP in [1.5,2.5]:", min(cs), max(cs))
# fits with all (c0,c1,k1,k2) free at B=2 -> sigma(c0)
print("  (c0,c1,k1,k2) B=2:", M.fmt(M.fit(y, cov, b, a, ["c0", "c1", "k1", "k2"])))
print("  (c0,k1,B_NP free):", M.fmt(M.fit(y, cov, b, a, ["c0", "k1"], BNP_free=True)))
