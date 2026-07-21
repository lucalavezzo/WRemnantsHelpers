"""Is the tail gap the bT-NODE DENSITY of the grid the spline is built on?

compare_cache_vs_scetlib showed: SCETlib's OWN W_full Hankeled on the 2000-node cache grid
-> 0.444*sval at qT=100, but on a 6000-node grid -> 0.977*sval. W is smooth, so if the base
node density were sufficient both would agree. Here: fresh SCETlib W_full at (91,0,qT), sampled
on logspace(bmin,bmax,N) for growing N, splined, Hankeled with the SAME fine simpson.

If h/sval climbs 0.44 -> ~0.98 with N, the cache's 2000 bT nodes are too coarse to represent
the integrand for the deep-tail Hankel (the ~486x cancellation eats the spline error).
The residual ~0.977 (not 1.0) is the finite-real-b Hankel vs SCETlib DE method gap.

Run: v15 container (scetlib_core), source /opt/env.sh, hist stub on PYTHONPATH, bind /cvmfs.
"""

import sys
import numpy as np

CARD = "/scratch/submit/cms/wmass/scetlib_np/pointmode_bT_converge/pm_default.ini"
FAC = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run"
BUILD = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/build/lib"
Q, Y = 91.0, 0.0
QTS = [90.0, 100.0]
NS = [2000, 4000, 8000, 16000, 32000, 64000]

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
    g = qT_mod.NPModelGammaNu()
    g.lambda_inf_nu = GNU["lambda_inf_nu"]
    g.lambda2_nu = GNU["lambda2_nu"]
    g.lambda4_nu = GNU["lambda4_nu"]
    if hasattr(g, "lambda6_nu"):
        g.lambda6_nu = GNU["lambda6_nu"]
    g.b0_bmax_nu = GNU["b0_bmax_nu"]
    g.np_model_nu = qT_mod.NPModelGammaNuModel.__members__[GNU["np_model_nu"]]
    sigma.set_gamma_nu_model_params(g)


def main():
    sys.path.insert(0, FAC)
    sys.path.insert(0, BUILD)
    from scetlib_run import config as scetlib_config
    import scetlib_qT as qT_mod
    from scipy.interpolate import CubicSpline
    from scipy.integrate import simpson
    from scipy.special import j0

    conf = scetlib_config.read_config(CARD)
    *_, sigma = scetlib_config.configure_calculation(conf)
    set_full_np(qT_mod, sigma)

    # cache grid params: logspace(1e-3, 50, 2000)
    bmin, bmax = 1e-3, 50.0
    for qt in QTS:
        sval = sigma(Q, Y, qt).val
        print(f"\n=== Q={Q} Y={Y} qT={qt}  sval(DE)={sval:.7g} ===")
        print(f"  {'N_nodes':>8} {'h':>13} {'h/sval':>9}")
        for N in NS:
            bT = np.logspace(np.log10(bmin), np.log10(bmax), N)
            W = np.asarray(
                sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float
            )
            spl = CubicSpline(bT, W)
            bf = np.linspace(bmin, bmax, 4_000_000)
            h = qt * simpson(bf * j0(qt * bf) * spl(bf), x=bf)
            print(f"  {N:>8,} {h:13.6g} {h/sval:9.4f}")
        # direct (no spline): sample W on the fine grid itself -> removes spline error entirely
        bf = np.logspace(np.log10(bmin), np.log10(bmax), 400_000)
        Wf = np.asarray(sigma.resummed_bT_integrand(Q, Y, qt, bf.tolist()), dtype=float)
        h_direct = qt * simpson(bf * j0(qt * bf) * Wf, x=bf)
        print(f"  direct400k(no spline)  h={h_direct:.6g}  h/sval={h_direct/sval:.4f}")


if __name__ == "__main__":
    main()
