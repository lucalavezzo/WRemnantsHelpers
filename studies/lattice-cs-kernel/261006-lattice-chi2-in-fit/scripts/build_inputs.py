#!/usr/bin/env python3
"""Build the frozen inputs of the in-fit lattice CS-kernel chi2 (lattice_cs_chi2.py) -> ../lattice_aswz_inputs.npz (+ .json).

Everything is taken from the validated pieces of this study, not retyped:
  data    260923-lattice-data-refit/cs_fit.py::load()  (ASWZ 2402.06725 per-ensemble L32/L48/L64, block-diagonal cov,
          21 points; NO cross-ensemble correlation, author-confirmed negligible 2026-09-29)
  pert    260923-scetlib-kernel-fit/kernel_fit.py::pert_tables() -> our_cs_kernel.py, scheme "fit" (n_f = 5), mu = 2 GeV,
          N3LL, alpha_s(mZ) = 0.118 (= the AD cache's alphas_mu0 / alphas_order n3ll), mu0 floor 1 GeV, sextic b*,
          b0/bmax_nu = 1. Validated against SCETlib Gamma_nu to 5e-11 (260923-conventions-map).
  model   gamma_zeta = pert + 1/2 gamma_nu^NP(bare b_T) + k1 a/b_T, gamma_nu^NP = -linf tanh((l2 u + l4 u^2 [+ l6 u^3])/linf),
          u = b_T^2 [GeV^-2]  (kernel_fit.np_zeta; the k1 term is the ASWZ lattice-spacing artefact)
  syst    the SAME three groups and the SAME chosen variants as the 2D card term
          (260923-lattice-fits/scripts/inject_aswz_cs_prior_theta.py::build_constraint): n_f scheme (nf matched at mu=1),
          k-form (k2 only), b_T window (drop b_T < 0.2 fm). Each chosen parameter shift d_g = (dl2, dl4) is mapped onto the
          points with the NP Jacobian at the lattice best fit, delta_g = J_NP d_g, and C_syst = sum_g delta_g delta_g^T is
          ADDED to the data covariance ("syst=J", default). By Woodbury, for a model linear in (l2, l4, k1),
          (J^T (V + J S J^T)^-1 J)^-1 = (J^T V^-1 J)^-1 + S: the profiled (l2, l4) covariance is exactly the card term's
          stat+syst covariance, and the best fit / chi2_min are unchanged. Away from the minimum the term stays the exact
          (tanh) chi2. Alternative "syst=direct_nf": the n_f group as the direct point shift pert(nf5 matched at mu=1) -
          pert(nf5), k-form and b_T window J-mapped as above.
Also stored: d pert / d alpha_s(mZ) and d pert / d TNP (gamma_nu, cusp) per point, for the caveat quantification.
"""

import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
STUDY = os.path.dirname(TASK)
KFD = os.path.join(STUDY, "260923-scetlib-kernel-fit")
INJ = os.path.join(
    STUDY, "260923-lattice-fits", "scripts", "inject_aswz_cs_prior_theta.py"
)
sys.path.insert(0, KFD)
sys.path.insert(0, HERE)
import kernel_fit as KF  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def jac_np(b_fm, linf, l2, l4):
    u = (np.asarray(b_fm) * KF.FM) ** 2
    s2 = 1.0 / np.cosh((l2 * u + l4 * u * u) / linf) ** 2
    return np.column_stack(
        [-0.5 * s2 * u, -0.5 * s2 * u * u]
    )  # d gamma_zeta^NP / d(l2, l4)


def main():
    D = KF.load_data()
    P = KF.pert_tables(D["b"])
    ref = np.load(os.path.join(KFD, "pert_tables.npz"))
    for k in ("nf5", "nf4", "nf5_mu1match"):
        assert np.allclose(P[k], ref[f"data_{k}"], rtol=0, atol=1e-12), k
    # alpha_s and TNP response of the perturbative table (central differences)
    lam0 = {"lambda_inf_nu": 0.0}
    h = 1e-4  # local derivative (h = 1e-3 carried a 0.75 % curvature bias; phase-2 check)
    pa = [
        KF.K.our_cs_kernel(D["b"], lam0, alphas_mz=0.118 + s * h, mu=2.0, scheme="fit")
        for s in (-1, 1)
    ]
    dpert_das = (pa[1] - pa[0]) / (2 * h)
    pt = [
        KF.K.our_cs_kernel(D["b"], lam0, mu=2.0, scheme="fit", tnp_nu=s * 0.5)
        for s in (-1, 1)
    ]
    dpert_dtnp_nu = (pt[1] - pt[0]) / 1.0
    pc = [
        KF.K.our_cs_kernel(D["b"], lam0, mu=2.0, scheme="fit", tnp_cusp=s * 0.5)
        for s in (-1, 1)
    ]
    dpert_dtnp_cusp = (pc[1] - pc[0]) / 1.0

    # phase 3 (fully live pert): second order in alpha_s and the alpha_s x TNP cross terms. The TNPs enter the kernel
    # exactly linearly (tnp_nu on the 3-loop gamma_nu boundary constant, tnp_cusp on Gamma_3); a central difference
    # with step 1 is therefore exact for them.
    def pk(a=0.118, tn=0.0, tc=0.0):
        return KF.K.our_cs_kernel(
            D["b"], lam0, alphas_mz=a, mu=2.0, scheme="fit", tnp_nu=tn, tnp_cusp=tc
        )

    h2 = 1e-3
    p0 = pk()
    dpert_dalphas2 = (pk(0.118 + h2) - 2 * p0 + pk(0.118 - h2)) / h2**2
    dpert_dtnp_nu1 = (pk(tn=1.0) - pk(tn=-1.0)) / 2.0
    dpert_dtnp_cusp1 = (pk(tc=1.0) - pk(tc=-1.0)) / 2.0
    dpert_das_tnp_nu = (
        (pk(0.118 + h2, 1.0) - pk(0.118 - h2, 1.0))
        - (pk(0.118 + h2, -1.0) - pk(0.118 - h2, -1.0))
    ) / (4 * h2)
    dpert_das_tnp_cusp = (
        (pk(0.118 + h2, 0.0, 1.0) - pk(0.118 - h2, 0.0, 1.0))
        - (pk(0.118 + h2, 0.0, -1.0) - pk(0.118 - h2, 0.0, -1.0))
    ) / (4 * h2)

    inj = _load("inj", INJ)
    mu, ctot, info = inj.build_constraint(inj.KFIT, "default")
    nom = json.load(open(inj.KFIT))[inj.NOMINAL]
    J = jac_np(D["b"], 2.0, nom["x"]["l2"], nom["x"]["l4"])
    groups, deltas = [], []
    for g, (variant, dv, c2) in info["chosen"].items():
        groups.append(f"{g}: {variant}")
        deltas.append(J @ np.asarray(dv))
    deltas = np.array(deltas)
    i_nf = [i for i, g in enumerate(groups) if g.startswith("n_f")][0]
    direct = deltas.copy()
    direct[i_nf] = P["nf5_mu1match"] - P["nf5"]

    # perturbative-kernel scale variation (2026-10-06 phase 2): b-space boundary scale mu0 -> kappa mu0, kappa = 2, 1/2
    # (floored scale varied too, "full"), a DIRECT point shift; the larger under the stat metric delta^T C_stat^-1 delta
    # is taken (one group, alternatives, as the injector does). Canonical-only and N4LL shifts stored for the record.
    import pert_scale as PS

    pn = PS.pert_var(KF.K, D["b"])
    assert np.max(np.abs(pn - P["nf5"])) < 1e-12
    Wst = np.linalg.inv(D["cov"])
    pv = {
        "kappa2_full": PS.pert_var(KF.K, D["b"], kappa=2.0) - pn,
        "kappa0.5_full": PS.pert_var(KF.K, D["b"], kappa=0.5) - pn,
        "kappa2_canonical": PS.pert_var(KF.K, D["b"], kappa=2.0, mode="canonical") - pn,
        "kappa0.5_canonical": PS.pert_var(KF.K, D["b"], kappa=0.5, mode="canonical")
        - pn,
        "n4ll": PS.pert_var(KF.K, D["b"], order="n4ll") - pn,
    }
    metric = {k: float(v @ Wst @ v) for k, v in pv.items()}
    chosen_pert = max(("kappa2_full", "kappa0.5_full"), key=lambda k: metric[k])
    syst_pert = pv[chosen_pert]

    out = dict(
        b_fm=D["b"],
        a_fm=D["a"],
        y=D["y"],
        ens=D["ens"],
        cov_stat=D["cov"],
        pert=P["nf5"],
        pert_nf4=P["nf4"],
        pert_nf5_mu1match=P["nf5_mu1match"],
        syst_J=deltas,
        syst_direct_nf=direct,
        syst_pert=syst_pert[None, :],
        **{f"pertvar_{k}": v for k, v in pv.items()},
        dpert_dalphas=dpert_das,
        dpert_dalphas2=dpert_dalphas2,
        dpert_dtnp_nu1=dpert_dtnp_nu1,
        dpert_dtnp_cusp1=dpert_dtnp_cusp1,
        dpert_das_tnp_nu=dpert_das_tnp_nu,
        dpert_das_tnp_cusp=dpert_das_tnp_cusp,
        dpert_dtnp_nu=dpert_dtnp_nu,
        dpert_dtnp_cusp=dpert_dtnp_cusp,
        card2d_mu=mu,
        card2d_cov=ctot,
        card2d_cstat=info["cstat"],
        card2d_csyst=info["csyst"],
        jac_ref=J,
        jac_ref_point=np.array([2.0, nom["x"]["l2"], nom["x"]["l4"]]),
        fm_to_gevinv=np.array(KF.FM),
    )
    np.savez(os.path.join(TASK, "lattice_aswz_inputs.npz"), **out)
    meta = dict(
        groups=groups,
        n=int(len(D["b"])),
        pert="our_cs_kernel scheme=fit (nf=5), mu=2 GeV, n3ll, alpha_s(mZ)=0.118",
        syst_rule="delta_g = J_NP(lattice best fit, linf=2) . d_g, d_g = injector's chosen (dl2, dl4) per group",
        card2d_mu=mu.tolist(),
        card2d_sigma=np.sqrt(np.diag(ctot)).tolist(),
        card2d_rho=float(ctot[0, 1] / np.sqrt(ctot[0, 0] * ctot[1, 1])),
        max_abs_dpert_dalphas=float(np.max(np.abs(dpert_das))),
        dpert_dalphas_range=[float(dpert_das.min()), float(dpert_das.max())],
        dpert_dtnp_nu_range=[float(dpert_dtnp_nu.min()), float(dpert_dtnp_nu.max())],
        dpert_dtnp_cusp_range=[
            float(dpert_dtnp_cusp.min()),
            float(dpert_dtnp_cusp.max()),
        ],
        syst_J_norm=np.linalg.norm(deltas, axis=1).tolist(),
        pert_scale_metric_stat=metric,
        pert_scale_chosen=chosen_pert,
        pert_scale_max_abs=float(np.max(np.abs(syst_pert))),
        pert_scale_max_over_sigma=float(
            np.max(np.abs(syst_pert) / np.sqrt(np.diag(D["cov"])))
        ),
        syst_direct_nf_norm=float(np.linalg.norm(direct[i_nf])),
    )
    json.dump(meta, open(os.path.join(TASK, "lattice_aswz_inputs.json"), "w"), indent=1)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
