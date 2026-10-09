"""BLNY check: paper L364-366 quotes g2=0.085(26) at B_NP=1.5, chi2/dof=0.58 for D_NP = g2 b^2."""

import numpy as np
import cs_fit as M

ens, D_ = M.load()
b, y, a, cov = D_["b"], D_["y"], D_["a"], D_["cov"]
bt = b * M.FM
for mode in ["numeric", "paper"]:
    for B in [1.5]:
        off, cols = M.design(b, a, B, mode)
        cols2 = dict(g2=-2.0 * bt**2, k1=cols["k1"], k2=cols["k2"])
        for free in [["g2"], ["g2", "k1"], ["g2", "k2"], ["g2", "k1", "k2"]]:
            th, C, chi2 = M.gls(y, cov, off, cols2, free)
            print(
                f"{mode:7s} B_NP={B} {str(free):20s} "
                + " ".join(
                    f"{p}={t:.4f}({e:.4f})"
                    for p, t, e in zip(free, th, np.sqrt(np.diag(C)))
                )
                + f" chi2/dof={chi2/(len(y)-len(free)):.3f}"
            )
