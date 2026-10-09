"""Validate our_cs_kernel.py against SCETlib's own qT::Gamma_nu (C++ driver).

Run inside the WRemnants singularity (the driver links the pinned SCETlib build):
    python test_our_cs_kernel.py
Writes test_our_cs_kernel.txt next to this file.
"""

import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import our_cs_kernel as K  # noqa: E402

DRIVER = os.path.join(HERE, "driver", "gamma_zeta_driver")
BT_FM = np.array([0.05, 0.1, 0.15, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 1.2])


def driver(
    nf,
    a_start,
    mu_start,
    order,
    lam,
    mu=2.0,
    npm=0,
    exact=False,
    tnp_nu=0.0,
    tnp_cusp=0.0,
):
    env = dict(
        os.environ,
        GZ_EXACT="1" if exact else "0",
        GZ_TNP_NU=str(tnp_nu),
        GZ_TNP_CUSP=str(tnp_cusp),
    )
    args = [
        DRIVER,
        str(nf),
        repr(float(a_start)),
        repr(float(mu_start)),
        str(order),
        "1",
        "1",
        "1",
        repr(mu),
        str(npm),
        repr(lam["lambda_inf_nu"]),
        repr(lam["lambda2_nu"]),
        repr(lam.get("lambda4_nu", 0.0)),
        repr(lam.get("lambda6_nu", 0.0)),
    ] + [repr(float(b * K.FM_TO_GEVINV)) for b in BT_FM]
    out = subprocess.run(
        args, capture_output=True, text=True, env=env, check=True
    ).stdout
    return np.loadtxt(out.splitlines()[1:])


def main():
    lam = K.AN_CRIDGE_TUNE
    lines = []
    worst = {}

    def check(tag, ref, py, tol):
        d = np.max(np.abs(ref - py))
        worst[tag] = (d, tol)
        lines.append(
            f"{tag:55s} max|py - C++| = {d:.2e}   (tol {tol:.0e})  {'PASS' if d < tol else 'FAIL'}"
        )

    # 1. fit scheme (nf=5 fixed) vs SCETlib exact running/RGE: must agree to numerical precision
    ref = driver(5, 0.118, K.MZ, 3, lam, exact=True)
    py = K.our_cs_kernel(BT_FM, lam, scheme="fit", parts=True)
    check("fit nf=5 N3LL full   vs C++ exact", ref[:, 6], py["full"], 1e-5)
    check("fit nf=5 N3LL pert   vs C++ exact", ref[:, 4], py["pert"], 1e-5)
    check("fit nf=5 N3LL mu0 (driver prints 8 dp)", ref[:, 1], py["mu0"], 1e-7)
    # 2. vs SCETlib's default ANALYTIC (re-expanded) solution -- the one the fit actually uses
    ref_an = driver(5, 0.118, K.MZ, 3, lam, exact=False)
    check(
        "fit nf=5 N3LL full   vs C++ analytic (fit default)",
        ref_an[:, 6],
        py["full"],
        3e-3,
    )
    # 3. lattice scheme (nf=4): give the driver the decoupled starting value
    cpl = K.Coupling(0.118, "lattice")
    ref4 = driver(4, cpl.a_ref, cpl.mu_ref, 3, lam, exact=True)
    py4 = K.our_cs_kernel(BT_FM, lam, scheme="lattice", coupling=cpl)
    check("lattice nf=4 N3LL full vs C++ exact (same start)", ref4[:, 6], py4, 1e-5)
    # 4. TNPs (fit parameters at N3+0LL)
    reft = driver(5, 0.118, K.MZ, 3, lam, exact=True, tnp_nu=1.0, tnp_cusp=1.0)
    pyt = K.our_cs_kernel(BT_FM, lam, scheme="fit", tnp_nu=1.0, tnp_cusp=1.0)
    check("fit nf=5 N3LL, theta_gnu=theta_cusp=1 vs C++ exact", reft[:, 6], pyt, 1e-5)
    # 5. tanh_6 NP form
    lam6 = dict(lam, lambda6_nu=0.01)
    ref6 = driver(5, 0.118, K.MZ, 3, lam6, npm=1, exact=True)
    py6 = K.our_cs_kernel(BT_FM, lam6, scheme="fit", np_model_nu="tanh_6")
    check("fit nf=5 N3LL tanh_6 vs C++ exact", ref6[:, 6], py6, 1e-5)
    # 6. N4LL (FO boundary through a_s^4; SCETlib has no 5-loop cusp)
    #    (SCETlib's exact solvers stop at N3LL, so compare to the analytic solution, loose tol)
    ref_n4 = driver(5, 0.118, K.MZ, 4, lam, exact=False)
    py_n4 = K.our_cs_kernel(BT_FM, lam, scheme="fit", order="n4ll")
    check("fit nf=5 N4LL full vs C++ analytic", ref_n4[:, 6], py_n4, 5e-3)
    # 7. mu dependence: d gamma_zeta / d ln mu = -2 Gamma_cusp(mu), Gamma_0 = 4 C_F  (NP piece mu-independent)
    h = 1e-3
    g_up = K.our_cs_kernel(
        [0.5], lam, mu=2.0 * np.exp(h), scheme="lattice", coupling=cpl
    )
    g_dn = K.our_cs_kernel(
        [0.5], lam, mu=2.0 * np.exp(-h), scheme="lattice", coupling=cpl
    )
    a = cpl(2.0) / (4 * np.pi)
    cusp = sum(g * a ** (n + 1) for n, g in enumerate(K._COEFFS[4]["cusp"]))
    check(
        "d gamma_zeta/d ln mu + 2 Gamma_cusp(2 GeV)",
        np.array([-2 * cusp]),
        (g_up - g_dn) / (2 * h),
        1e-5,
    )

    lines.append("")
    lines.append("bT[fm]  C++exact_fit  py_fit  C++analytic_fit  py_lattice(nf=4)")
    for i, b in enumerate(BT_FM):
        lines.append(
            f"{b:5.2f}  {ref[i,6]: .6f}  {py['full'][i]: .6f}  {ref_an[i,6]: .6f}  {py4[i]: .6f}"
        )
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(HERE, "test_our_cs_kernel.txt"), "w") as f:
        f.write(txt + "\n")
    if any(d >= tol for d, tol in worst.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
