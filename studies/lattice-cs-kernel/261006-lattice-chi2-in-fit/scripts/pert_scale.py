"""Perturbative-kernel scale variations of gamma_pert at the lattice points (our_cs_kernel internals, scheme fit, mu=2).
kappa scales the b-space boundary scale mu0 of the FO boundary + cusp evolution:
  mode "full":      mu0 -> kappa * mu0(b_T)                   (floored scale varied too)
  mode "canonical": mu0 -> ((kappa b0/b_T)^4 + mu0_min^4)^(1/4) (canonical part only; floor kept)
L_b = ln(mu0^2 b*^2 / b0^2) follows mu0, so the variation is the standard RG-consistent one.
"""

import numpy as np


def pert_var(
    K, b_fm, kappa=1.0, mode="full", order="n3ll", alphas_mz=0.118, mu=2.0, mu0_min=1.0
):
    n_order = K._ORDER[order]
    cpl = K.Coupling(alphas_mz, "fit", nloop=min(n_order + 1, 5))
    out = []
    for bT in np.atleast_1d(b_fm) * K.FM_TO_GEVINV:
        if mode == "full":
            mu0 = kappa * K.mu0_of_bT(bT, mu0_min)
        elif mode == "canonical":
            mu0 = ((kappa * K.B0 / bT) ** 4 + mu0_min**4) ** 0.25
        else:
            raise ValueError(mode)
        a0 = cpl(mu0) / (4 * np.pi)
        Lb = 2.0 * np.log(mu0 * K.bstar_over_b0(bT, 1.0))
        gnu = -4.0 * K.eta_cusp(cpl, mu0, mu, cpl.nf, n_order) + K._gnu_fo(
            Lb, a0, cpl.nf, n_order
        )
        out.append(0.5 * gnu)
    return np.array(out)
