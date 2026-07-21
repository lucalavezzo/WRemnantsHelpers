"""CLINCHER: is the high-qT gap the NP-factorization (integrand differs) or SCETlib's
DE bT-integration (contour/method)?

Build SCETlib with NP ON (franksvals, from pm_default.ini) WITHOUT force_np_off, then at
(Q=91,Y=0,qT in tail):
  W_scetlib(bT) = sigma.resummed_bT_integrand(Q,Y,qT,bT)   # SCETlib's NP-ON integrand
  sval          = sigma(Q,Y,qT).val                         # SCETlib's DE bT integral
  my_hankel     = qT * ∫ bT J0(qT bT) W_scetlib dbT          # MY converged integrator, SAME integrand
Compare:
  my_hankel == sval   -> SCETlib's DE integrator == real-b Hankel of its own integrand
                         (so our earlier 0.444 gap is because OUR reconstructed integrand
                          W_ours != W_scetlib, i.e. the bt-grid NP factorization).
  my_hankel != sval, ~our 0.444 -> SCETlib's DE integrator computes a different value than
                         the real-b Hankel of the SAME integrand (contour/method).
Also dumps W_scetlib vs a naive check so we can see where they diverge.

Run: v15 container + `source /opt/env.sh` + hist stub on PYTHONPATH.
"""

import sys
import numpy as np

CARD = "/scratch/submit/cms/wmass/scetlib_np/pointmode_bT_converge/pm_default.ini"
FAC = "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/prod/scetlib_run"
QTS = [60.0, 85.0, 90.0, 95.0, 100.0]
Q, Y = 91.0, 0.0


def main():
    sys.path.insert(0, FAC)
    sys.path.insert(
        0, "/work/submit/lavezzo/alphaS/scetlib-cms-newnp-lambda4fix/build/lib"
    )
    from scetlib_run import config as scetlib_config
    import scetlib_qT as qT_mod
    from scipy.special import j0
    from scipy.integrate import simpson

    conf = scetlib_config.read_config(CARD)
    order, alphas, decay, scales, sigma = scetlib_config.configure_calculation(conf)
    # NP is ON (from the card's [Nonperturbative]); we do NOT call force_np_off.
    if not isinstance(sigma, qT_mod.DrellYan):
        raise RuntimeError("expected DrellYan")

    # bT grid to sample the NP-on integrand (dense; then Hankel with a fine grid)
    bT = np.logspace(-3, np.log10(50.0), 4000)
    bT_fine = np.linspace(bT.min(), bT.max(), 800_000)
    from scipy.interpolate import CubicSpline

    print(
        f"{'qT':>6} {'sval(DE)':>13} {'my_hankel':>13} {'myH/sval':>10} {'sval/myH':>10}"
    )
    for qt in QTS:
        W = np.asarray(sigma.resummed_bT_integrand(Q, Y, qt, bT.tolist()), dtype=float)
        sval = sigma(Q, Y, qt).val
        Wf = CubicSpline(bT, W)(bT_fine)
        myH = qt * simpson(bT_fine * j0(qt * bT_fine) * Wf, x=bT_fine)
        print(f"{qt:6.1f} {sval:13.6g} {myH:13.6g} {myH/sval:10.4f} {sval/myH:10.4f}")


if __name__ == "__main__":
    main()
