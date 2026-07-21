"""Root cause: the small-bT LOWER LIMIT of the grid, not density/bmax.

First run showed bmin=1e-5 -> 0.9989*sval but bmin=1e-3 (the cache grid start) -> 0.4444,
at qT=100. Here: ONE SCETlib sampling of W_full on a master log grid [1e-6, 60] (avoids the
fragile repeated 4M-point calls), spline it (W is smooth in bT), then do all range/cumulative
analysis in numpy. Confirms which endpoint flips the deep-tail Hankel and localizes the
missing contribution.

Run: v15 container (scetlib_core), source /opt/env.sh, hist stub on PYTHONPATH, bind /cvmfs.
"""

import sys
import numpy as np

CARD = "/scratch/submit/cms/wmass/scetlib_np/pointmode_bT_converge/pm_default.ini"
FAC = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run"
BUILD = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/build/lib"
Q, Y = 91.0, 0.0
QTS = [90.0, 100.0]
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

    # ONE master sampling of W (smooth in bT) on a wide log grid
    bT_m = np.logspace(-6, np.log10(60.0), 40000)
    svals = {qt: sigma(Q, Y, qt).val for qt in QTS}
    dump = {"bT_m": bT_m}

    for qt in QTS:
        W_m = np.asarray(
            sigma.resummed_bT_integrand(Q, Y, qt, bT_m.tolist()), dtype=float
        )
        spl = CubicSpline(bT_m, W_m)
        sval = svals[qt]
        dump[f"W_m_{qt:.0f}"] = W_m
        dump[f"sval_{qt:.0f}"] = sval
        print(f"\n================ qT={qt}  sval(DE)={sval:.7g} ================")

        def hankel(bmin, bmax, Nfine=3_000_000):
            bf = np.linspace(bmin, bmax, Nfine)
            return qt * simpson(bf * j0(qt * bf) * spl(bf), x=bf)

        print("  -- vary bmin (bmax=50) --")
        for bmin in [1e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]:
            print(f"     [{bmin:.0e}, 50]  h/sval = {hankel(bmin,50.0)/sval:.4f}")
        print("  -- vary bmax (bmin=1e-6) --")
        for bmax in [30.0, 40.0, 50.0, 60.0]:
            print(f"     [1e-6, {bmax:.0f}]  h/sval = {hankel(1e-6,bmax)/sval:.4f}")

        # integrand magnitude at small bT
        if qt == 100.0:
            print("  -- W and bf*J0*W at small bT --")
            for b in [1e-6, 1e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 0.1, 0.3, 1.0]:
                w = float(spl(b))
                ig = b * j0(qt * b) * w
                print(f"     bT={b:9.1e}  W={w:14.6g}  bf*J0*W={ig:14.6g}")
            print("  -- cumulative qT*int_1e-6^X --")
            bf = np.linspace(1e-6, 50.0, 3_000_000)
            integrand = qt * bf * j0(qt * bf) * spl(bf)
            for X in [
                1e-4,
                3e-4,
                1e-3,
                3e-3,
                1e-2,
                3e-2,
                0.1,
                0.3,
                1.0,
                3.0,
                10.0,
                50.0,
            ]:
                m = bf <= X
                part = simpson(integrand[m], x=bf[m])
                print(f"     int_1e-6^{X:<7} = {part:12.6g}   /sval = {part/sval:.4f}")

    OUT = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ptvgen-truncation/btgrid_range_isolation.npz"
    np.savez(OUT, **dump)
    print(f"\nsaved -> {OUT}")


if __name__ == "__main__":
    main()
