"""Quick-verify the min=1e-6 fix (SAMPLING half, v15): cache exactly what `generate` caches.

For several (bmin, N) bT grids, sample at (Q=91,Y=0, qT in {90,95,100}):
  I_pert[bin, bT] = resummed_bT_integrand with NP OFF but the perturbative gamma_nu kernel
                    kept (b0_bmax_nu=1, np_model_nu=tanh_2) -- matches bt_grid.force_np_off.
  C_nu[bin, bT]   = gamma_nu_NP_log_coeff
  b_bar[bT]       = b_star_global(bT)
  sval[qT]        = sigma(Q,Y,qT).val  (full franksvals NP, DE integrator = truth)
Saved per grid -> reconstruct in the wremnants container with the REAL btgrid_tf.reconstruct.

Grids: control (1e-3,2000) must reproduce ~0.44; fix candidates extend bmin to 1e-5/1e-6.

Run: v15 container (scetlib_core), source /opt/env.sh, hist stub on PYTHONPATH, bind /cvmfs.
"""

import sys
import numpy as np

CARD = "/scratch/submit/cms/wmass/scetlib_np/pointmode_bT_converge/pm_default.ini"
FAC = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run"
BUILD = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/build/lib"
OUT = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/verify_fix_sample.npz"
Q, Y = 91.0, 0.0
QTS = [90.0, 95.0, 100.0]
GRIDS = [
    ("1e-3_2k", 1e-3, 2000),
    ("1e-6_3k", 1e-6, 3000),
    ("1e-6_4k", 1e-6, 4000),
    ("1e-6_5k", 1e-6, 5000),
    ("1e-6_6k", 1e-6, 6000),
    ("1e-6_8k", 1e-6, 8000),
    ("1e-6_12k", 1e-6, 12000),
    ("1e-6_16k", 1e-6, 16000),
]

FEFF = dict(
    lambda_inf=1.0,
    lambda2=0.4,
    delta_lambda2=0.0,
    lambda4=0.4,
    lambda6=0.016,
    np_model="tanh_2",
)
GNU = dict(
    lambda_inf_nu=2.0,
    lambda2_nu=0.15,
    lambda4_nu=0.0,
    lambda6_nu=0.0007,
    b0_bmax_nu=1.0,
    np_model_nu="tanh_2",
)


def set_full_np(qT_mod, sigma):
    m = qT_mod.NPModelEffective()
    m.lambda_inf = FEFF["lambda_inf"]
    m.lambda2 = FEFF["lambda2"]
    m.delta_lambda2 = FEFF["delta_lambda2"]
    m.lambda4 = FEFF["lambda4"]
    m.lambda6 = FEFF["lambda6"]
    m.np_model = qT_mod.NPModelEffectiveModel.__members__[FEFF["np_model"]]
    sigma.set_effective_model(m)
    _set_gnu(qT_mod, sigma, np_on=True)


def _set_gnu(qT_mod, sigma, np_on):
    g = qT_mod.NPModelGammaNu()
    g.b0_bmax_nu = GNU["b0_bmax_nu"]  # keep perturbative b* kernel
    g.np_model_nu = qT_mod.NPModelGammaNuModel.__members__[GNU["np_model_nu"]]
    if np_on:
        g.lambda_inf_nu = GNU["lambda_inf_nu"]
        g.lambda2_nu = GNU["lambda2_nu"]
        g.lambda4_nu = GNU["lambda4_nu"]
        if hasattr(g, "lambda6_nu"):
            g.lambda6_nu = GNU["lambda6_nu"]
    else:
        g.lambda2_nu = 0.0
        g.lambda4_nu = 0.0
        g.lambda_inf_nu = GNU["lambda_inf_nu"]  # lambdas=0 -> model=0
        if hasattr(g, "lambda6_nu"):
            g.lambda6_nu = 0.0
    sigma.set_gamma_nu_model_params(g)


def set_np_off_pert(qT_mod, sigma):
    sigma.set_effective_model(qT_mod.NPModelEffective())  # identity -> F_eff==1
    _set_gnu(qT_mod, sigma, np_on=False)  # gamma_nu NP=0, but b0_bmax_nu=1 kept


def main():
    sys.path.insert(0, FAC)
    sys.path.insert(0, BUILD)
    from scetlib_run import config as scetlib_config
    import scetlib_qT as qT_mod

    conf = scetlib_config.read_config(CARD)
    *_, sigma = scetlib_config.configure_calculation(conf)

    # DE truth (full NP)
    set_full_np(qT_mod, sigma)
    svals = np.array([sigma(Q, Y, qt).val for qt in QTS])

    dump = {
        "qTs": np.array(QTS),
        "svals": svals,
        "grid_names": np.array([g[0] for g in GRIDS]),
    }
    for name, bmin, N in GRIDS:
        bT = np.logspace(np.log10(bmin), np.log10(50.0), N)
        set_np_off_pert(qT_mod, sigma)
        I_pert = np.stack(
            [
                np.asarray(sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), float)
                for qt in QTS
            ]
        )
        C_nu = np.stack(
            [
                np.asarray(sigma.gamma_nu_NP_log_coeff(Q, Y, qt, bT.tolist()), float)
                for qt in QTS
            ]
        )
        b_bar = np.asarray(sigma.b_star_global(bT.tolist()), float)
        dump[f"bT_{name}"] = bT
        dump[f"Ipert_{name}"] = I_pert
        dump[f"Cnu_{name}"] = C_nu
        dump[f"bbar_{name}"] = b_bar
        print(
            f"[{name}] bmin={bmin:g} N={N}  sampled I_pert{I_pert.shape}, C_nu{C_nu.shape}"
        )

    np.savez(OUT, **dump)
    print(f"svals(DE) = {dict(zip(QTS, svals))}")
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
