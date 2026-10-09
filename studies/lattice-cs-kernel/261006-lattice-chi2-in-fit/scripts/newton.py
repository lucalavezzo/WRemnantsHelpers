#!/usr/bin/env python3
"""Cache-free Newton prediction of the exact-lattice fit from NOMSTIFF (same construction as T8's eval_l4nu_pull.py,
re-using ITS stored HVP column along lambda4_nu and gradient at NOMSTIFF on the 2D card, read-only):
  H = inv(C_NOMSTIFF) [data + priors + 1D term + engaged stiff spring]  - 1D lattice curvature + EXACT lattice Hessian
      (lambda2_nu, lambda4_nu block, theta units, syst=J), bordered by the data part of the HVP column
      (HVP - 2D card term column).
  g = data gradient at NOMSTIFF (2D-card gradient - 2D term gradient) + exact lattice gradient.
Quadratic, from one point: an orientation for the fit, not a result. Writes ../newton.json; alphaS only in sigma_NOM.
"""
import json
import os
import sys

import h5py
import numpy as np
from rabbit import io_tools

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import lattice_cs_chi2 as L  # noqa: E402

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOMSTIFF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
HVP = f"{A}/261006_t8_l4nu_lattice2d/l4nu_hvp_column_at_NOMSTIFF.npz"
CARDS = {
    k: f"{A}/260923_lattice_fits/cards/cardA_latticeASWZ_{v}.hdf5"
    for k, v in (("1d", "l4zero_statsyst"), ("2d", "statsyst"))
}


def ext_term(card):
    with h5py.File(card, "r") as f:
        t = f["external_terms/lattice_cs"]
        g = t["grad_values"][...].reshape(t["grad_values"].attrs["original_shape"])
        H = t["hess_dense"][...].reshape(t["hess_dense"].attrs["original_shape"])
    return g, H


def main():
    fr = io_tools.get_fitresult(NOMSTIFF, None)
    h = fr["parms"].get()
    nN = [str(n) for n in h.axes[0]]
    xN = np.asarray(h.values(), float)
    covN = np.asarray(fr["cov"].get().values(), float)
    z = np.load(HVP)
    names, hcol, grad = list(z["names"].astype(str)), z["hcol"], z["grad"]
    i2, i4 = names.index("lambda2_nu"), names.index("lambda4_nu")
    idx = np.array([names.index(n) for n in nN])
    g1, H1 = ext_term(CARDS["1d"])
    g2, H2 = ext_term(CARDS["2d"])
    t2, t4 = xN[nN.index("lambda2_nu")], 0.0
    # data parts (2D card minus its term)
    gd = grad.copy()
    gd[[i2, i4]] -= g2 + H2 @ np.array([t2, t4])
    hd = hcol.copy()
    hd[[i2, i4]] -= H2[:, 1]
    core = L.LatticeCSCore(syst="J")
    off = core.fit()[0].fun

    def nll_lat(a, b):  # theta of lambda2_nu, lambda4_nu
        return 0.5 * (
            core.chi2(
                dict(lambda_inf_nu=2.0, lambda2_nu=0.15 + 0.1 * a, lambda4_nu=0.5 * b)
            )
            - off
        )

    e = 1e-4
    gl = np.array(
        [
            (nll_lat(t2 + e, t4) - nll_lat(t2 - e, t4)) / (2 * e),
            (nll_lat(t2, t4 + e) - nll_lat(t2, t4 - e)) / (2 * e),
        ]
    )
    Hl = np.zeros((2, 2))
    f0 = nll_lat(t2, t4)
    Hl[0, 0] = (nll_lat(t2 + e, t4) - 2 * f0 + nll_lat(t2 - e, t4)) / e**2
    Hl[1, 1] = (nll_lat(t2, t4 + e) - 2 * f0 + nll_lat(t2, t4 - e)) / e**2
    Hl[0, 1] = Hl[1, 0] = (
        nll_lat(t2 + e, t4 + e)
        - nll_lat(t2 + e, t4 - e)
        - nll_lat(t2 - e, t4 + e)
        + nll_lat(t2 - e, t4 - e)
    ) / (4 * e * e)
    S = np.linalg.inv(covN)
    j2 = nN.index("lambda2_nu")
    S[j2, j2] += -H1[0, 0] + Hl[0, 0]
    b = hd[idx].copy()
    b[j2] += Hl[0, 1]
    c44 = hd[i4] + Hl[1, 1]
    Hf = np.block([[S, b[:, None]], [b[None, :], np.array([[c44]])]])
    gf = np.concatenate([gd[idx], [gd[i4]]])
    gf[j2] += gl[0]
    gf[-1] += gl[1]
    d = -np.linalg.solve(Hf, gf)
    C = np.linalg.inv(Hf)
    ja = nN.index("alphaS")
    sN = np.sqrt(covN[ja, ja])
    out = dict(
        lattice_grad_theta=gl.tolist(),
        lattice_hess_theta=Hl.tolist(),
        data_grad_l4_theta=float(gd[i4]),
        lambda2_nu=float(0.15 + 0.1 * (t2 + d[j2])),
        lambda4_nu=float(0.5 * d[-1]),
        dalphaS_over_sigNOM=float(d[ja] / sN),
        sigma_ratio=float(np.sqrt(C[ja, ja]) / sN),
        dNLL_pred=float(0.5 * gf @ d),
        tmd_dtheta={
            n: float(d[nN.index(n)]) for n in ("lambda2", "lambda4", "delta_lambda2")
        },
        lat_dchi2_at_pred=float(2 * nll_lat(t2 + d[j2], d[-1])),
    )
    print(json.dumps(out, indent=1))
    json.dump(out, open(os.path.join(TASK, "newton.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
