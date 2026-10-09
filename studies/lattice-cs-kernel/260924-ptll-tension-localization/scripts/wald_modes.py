"""Wald view of the wanted ptll shape: which correlated modes of the sub-fit covariance carry the deviation.
Reads wanted_shape.json is not enough (needs the covariance), so recompute via plot_wanted_shape.shape().
"""

import sys, os, numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_wanted_shape import shape, EDGES

for tag in ["FRZAS", "FRZASNP"]:
    R, e, CR, q, edm, P = shape(tag)
    d = R - 1
    w, V = np.linalg.eigh(CR)
    keep = w > 1e-12 * w.max()
    z = (V[:, keep].T @ d) / np.sqrt(w[keep])
    print(
        f"== {tag}: q_LR={q:.2f}  Wald d^T CR^+ d = {np.sum(z**2):.2f} on {keep.sum()} modes; "
        f"median per-bin corr = {np.median(np.abs((CR/np.outer(e,e))[np.triu_indices(39,1)])):.3f}"
    )
    order = np.argsort(-(z**2))[:4]
    for k in order:
        vec = V[:, keep][:, k]
        print(
            f"   mode sigma={100*np.sqrt(w[keep][k]):.3f}%  z^2={z[k]**2:.1f}  shape(0-1,2-2.5,4-4.5,7-7.5,12-13,20-22,37-44)="
            + " ".join(f"{vec[i]:+.2f}" for i in [0, 4, 8, 14, 24, 32, 38])
        )

# full contribution of the dominant mode to the wanted shape, in %
for tag in ["FRZAS", "FRZASNP"]:
    R, e, CR, q, edm, P = shape(tag)
    d = R - 1
    w, V = np.linalg.eigh(CR)
    keep = w > 1e-12 * w.max()
    Vk, wk = V[:, keep], w[keep]
    z = (Vk.T @ d) / np.sqrt(wk)
    k = np.argmax(z**2)
    contrib = z[k] * np.sqrt(wk[k]) * Vk[:, k]
    print(f"{tag} dominant-mode contribution to (R-1) [%], z^2={z[k]**2:.1f}:")
    print("  " + " ".join(f"{EDGES[i]:g}:{100*contrib[i]:+.2f}" for i in range(39)))
