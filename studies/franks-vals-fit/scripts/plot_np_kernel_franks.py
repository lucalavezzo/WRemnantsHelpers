"""Plot the SCETlib NP CS kernel and TMD boundary condition for the
FranksVals tanh_2 configuration, from a fitresults.hdf5 (with 68% toy
band from the postfit covariance).

FranksVals tanh_2 functional forms (no lambda_6 / Lambda_6 / b_T^5 tail
- the AN's tanh_6cs adds those; tanh_2 drops them).  Constants below
are the FranksVals fixed values:

    gamma_NP(b_T)   = -(lambda_inf_nu/2) * tanh[A(b_T)/lambda_inf_nu]
    A(b_T)          = lambda_2_nu * b_T^2 + lambda_4_nu * b_T^4
                      (lambda_4_nu = 0 fixed)

    f_NP(b_T, y)    = exp[ -2 * Lambda_inf * b_T * tanh(B(b_T,y)/Lambda_inf) ]
    B(b_T, y)       = L_2(y) * b_T + c_1(y)/3 * b_T^3
                      L_2(y) = Lambda_2 + Delta_Lambda_2 * y^2
                      c_1(y) = 3 * Lambda_4 + L_2(y)^3

    lambda_inf_nu = 2.0,  lambda_4_nu = 0.0 (fixed)
    Lambda_inf    = 1.0  (fixed)

The 4 FranksVals NPs that float: scetlibNPgammaLambda2 -> lambda_2_nu;
chargeVgenNP0scetlibNPZlambda2 -> Lambda_2; ...delta_lambda2 ->
Delta_Lambda_2; ...lambda4 -> Lambda_4.  Linearization map at
np_param_map_franks.json next to this script.
"""

import argparse, json, os, sys
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PMAP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "np_param_map_franks.json"
)

# FranksVals fixed constants.
LAMBDA_INF_NU = 2.0  # CS lambda_inf, fixed
LAMBDA_4_NU = 0.0  # CS lambda_4, fixed
LAMBDA_INF = 1.0  # TMD Lambda_inf, fixed
# No b_T^6 / b_T^5 tail in tanh_2.
LAMBDA_6_CS = 0.0
LAMBDA_6_TMD = 0.0

# Reference: FranksVals "prefit" centrals (np_model = tanh_2 inputs).
PREFIT = dict(
    lambda_2_nu=0.15,
    lambda_4_nu=LAMBDA_4_NU,
    lambda_inf_nu=LAMBDA_INF_NU,
    Lambda_2=0.40,
    Delta_Lambda_2=0.0,
    Lambda_4=0.40,
)


def gamma_NP(bT, p):
    A = p["lambda_2_nu"] * bT**2 + p["lambda_4_nu"] * bT**4 + LAMBDA_6_CS * bT**6
    return -0.5 * p["lambda_inf_nu"] * np.tanh(A / p["lambda_inf_nu"])


def f_NP(bT, y, p):
    L2y = p["Lambda_2"] + p["Delta_Lambda_2"] * y**2
    c1y = 3.0 * p["Lambda_4"] + L2y**3
    B = L2y * bT + (c1y / 3.0) * bT**3 + LAMBDA_6_TMD * bT**5
    return np.exp(-2.0 * LAMBDA_INF * bT * np.tanh(B / LAMBDA_INF))


# Map: rabbit nuisance name -> physical-key name in gamma_NP / f_NP dicts.
NP_NUIS = [
    "scetlibNPgammaLambda2",  # CS lambda_2_nu
    "chargeVgenNP0scetlibNPZlambda2",  # TMD Lambda_2
    "chargeVgenNP0scetlibNPZdelta_lambda2",  # TMD Delta_Lambda_2
    "chargeVgenNP0scetlibNPZlambda4",  # TMD Lambda_4
]
NP_PHYS_KEY = ["lambda_2_nu", "Lambda_2", "Delta_Lambda_2", "Lambda_4"]


def _theta_to_physical(theta, nuis, kfactor):
    with open(PMAP_PATH) as f:
        pmap = json.load(f)["nuisances"][nuis]
    nom = pmap["nominal"]
    d_up = (pmap["Up_template_value"] - nom) * kfactor
    d_dn = (nom - pmap["Down_template_value"]) * kfactor
    return nom + np.maximum(theta, 0) * d_up - np.maximum(-theta, 0) * d_dn


def sample_toys(fitresults_path, kfactors, n_toys, seed=0):
    sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
    sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
    from rabbit.io_tools import get_fitresult

    fr, _ = get_fitresult(fitresults_path, meta=True)
    parms = fr["parms"].get()
    names = list(parms.axes[0])
    cov_h = fr["cov"].get()
    cov_names = list(cov_h.axes[0])
    cov = cov_h.values()

    theta = np.zeros(len(NP_NUIS))
    cov_idx = []
    for k, nm in enumerate(NP_NUIS):
        if nm in names:
            theta[k] = float(parms.values()[names.index(nm)])
        if nm in cov_names:
            ci = cov_names.index(nm)
            if cov[ci, ci] > 0:
                cov_idx.append((k, ci))

    def _kf(k):
        return kfactors.get(NP_NUIS[k], kfactors.get(NP_PHYS_KEY[k], 1.0))

    central_phys = dict(PREFIT)  # start from FranksVals fixed centrals
    for k in range(len(NP_NUIS)):
        central_phys[NP_PHYS_KEY[k]] = float(
            _theta_to_physical(theta[k], NP_NUIS[k], _kf(k))
        )

    rng = np.random.default_rng(seed)
    if cov_idx:
        means = np.array([theta[k] for k, _ in cov_idx])
        sub = cov[np.ix_([ci for _, ci in cov_idx], [ci for _, ci in cov_idx])]
        toys_sub = rng.multivariate_normal(means, sub, size=n_toys)
    else:
        toys_sub = np.zeros((n_toys, 0))

    toys_theta = np.tile(theta, (n_toys, 1))
    for j, (k, _) in enumerate(cov_idx):
        toys_theta[:, k] = toys_sub[:, j]

    toys_phys = []
    for t in range(n_toys):
        d = dict(PREFIT)
        for k in range(len(NP_NUIS)):
            d[NP_PHYS_KEY[k]] = float(
                _theta_to_physical(toys_theta[t, k], NP_NUIS[k], _kf(k))
            )
        toys_phys.append(d)
    return central_phys, toys_phys


def parse_kfactor_args(args):
    out = {}
    for tok in args or []:
        k, v = tok.split("=", 1)
        out[k] = float(v)
    return out


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--from-fitresults",
        required=True,
        help="Path to fitresults.hdf5 (postfit + cov for the 4 FranksVals NPs)",
    )
    p.add_argument(
        "--kfactor",
        nargs="*",
        default=[],
        help="Per-NP kfactor overrides as NAME=K, e.g. scetlibNPgammaLambda2=5 "
        "or lambda_2_nu=5. Use when fit was built with --scaleParams.",
    )
    p.add_argument("--n-toys", type=int, default=500)
    p.add_argument("--label", default="postfit")
    p.add_argument("--y", type=float, nargs="+", default=[0.0, 2.5])
    p.add_argument("--bT-max", type=float, default=4.0)
    p.add_argument("--outpath", "-o", required=True)
    args = p.parse_args()

    kfactors = parse_kfactor_args(args.kfactor)
    point, toys = sample_toys(args.from_fitresults, kfactors, args.n_toys)
    print(f"Loaded postfit from {args.from_fitresults}")
    for k in (
        "lambda_2_nu",
        "lambda_4_nu",
        "lambda_inf_nu",
        "Lambda_2",
        "Delta_Lambda_2",
        "Lambda_4",
    ):
        print(f"  {k:<18s} = {point[k]:+.4f}")

    bT = np.linspace(0, args.bT_max, 401)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.5))

    # 68% toy bands on gamma_NP and f_NP per y.
    band_cs = None
    band_tmd = {}
    if toys:
        gamma_vals = np.array([gamma_NP(bT, t) for t in toys])
        band_cs = (
            np.percentile(gamma_vals, 16, axis=0),
            np.percentile(gamma_vals, 84, axis=0),
        )
        for y in args.y:
            fvals = np.array([f_NP(bT, y, t) for t in toys])
            band_tmd[y] = (
                np.percentile(fvals, 16, axis=0),
                np.percentile(fvals, 84, axis=0),
            )

    # Left panel: CS gamma_NP(b_T)
    axL.plot(bT, gamma_NP(bT, PREFIT), label="FranksVals prefit", color="C0", lw=2)
    if band_cs is not None:
        axL.fill_between(
            bT,
            band_cs[0],
            band_cs[1],
            color="C3",
            alpha=0.25,
            label=f"{args.label} 68% band ({args.n_toys} toys)",
        )
    axL.plot(bT, gamma_NP(bT, point), label=args.label, color="C3", lw=2)
    axL.axhline(0, color="k", lw=0.5)
    axL.axhline(
        -0.5 * LAMBDA_INF_NU,
        color="C0",
        ls=":",
        lw=1,
        label=rf"asymptote $-\lambda_{{\infty,\nu}}/2$ = {-0.5*LAMBDA_INF_NU:.2f}",
    )
    axL.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
    axL.set_ylabel(r"$\tilde\gamma^{\rm NP}(b_T)$")
    axL.set_title(
        r"$\tilde\gamma^{\rm NP}(b_T) = -\frac{\lambda_{\infty,\nu}}{2}\,"
        r"\tanh[\,(\lambda_{2,\nu} b_T^2 + \lambda_{4,\nu} b_T^4)/\lambda_{\infty,\nu}\,]$  (tanh\_2)",
        fontsize=10,
    )
    axL.legend(loc="lower left", fontsize=9)
    axL.grid(alpha=0.3)

    # Right panel: TMD f_NP(b_T, y)
    cmap_P = plt.cm.Reds
    cmap_0 = plt.cm.Blues
    n = len(args.y)
    for i, y in enumerate(args.y):
        shade = 0.4 + 0.5 * (i / max(n - 1, 1))
        axR.plot(
            bT,
            f_NP(bT, y, PREFIT),
            color=cmap_0(shade),
            lw=2,
            label=f"FranksVals prefit, y={y}",
        )
        if y in band_tmd:
            lo, hi = band_tmd[y]
            axR.fill_between(bT, lo, hi, color=cmap_P(shade), alpha=0.20)
        axR.plot(
            bT,
            f_NP(bT, y, point),
            color=cmap_P(shade),
            lw=2,
            ls="--",
            label=f"{args.label}, y={y}",
        )
    axR.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
    axR.set_ylabel(r"$f^{\rm NP}(b_T, y)$")
    axR.set_title(
        r"$f^{\rm NP}(b_T,y) = \exp[-2\Lambda_\infty b_T \tanh(B/\Lambda_\infty)]$,  "
        r"$B = L_2(y) b_T + \frac{c_1(y)}{3} b_T^3$  (tanh\_2)",
        fontsize=9,
    )
    axR.legend(loc="upper right", fontsize=8)
    axR.grid(alpha=0.3)

    box = dict(boxstyle="round,pad=0.35", fc="white", ec="0.6", alpha=0.85)
    cs_text = (
        f"$\\lambda_{{2,\\nu}} = {point['lambda_2_nu']:+.4f}$\n"
        f"$\\lambda_{{4,\\nu}} = {point['lambda_4_nu']:+.4f}$ (fixed)\n"
        f"$\\lambda_{{\\infty,\\nu}} = {point['lambda_inf_nu']:+.4f}$ (fixed)"
    )
    tmd_text = (
        f"$\\Lambda_2 = {point['Lambda_2']:+.4f}$\n"
        f"$\\Delta\\Lambda_2 = {point['Delta_Lambda_2']:+.4f}$\n"
        f"$\\Lambda_4 = {point['Lambda_4']:+.4f}$\n"
        f"$\\Lambda_\\infty = {LAMBDA_INF}$ (fixed)"
    )
    axL.text(
        0.97,
        0.55,
        cs_text,
        transform=axL.transAxes,
        fontsize=8,
        va="top",
        ha="right",
        bbox=box,
    )
    axR.text(
        0.97,
        0.55,
        tmd_text,
        transform=axR.transAxes,
        fontsize=8,
        va="top",
        ha="right",
        bbox=box,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.outpath)) or ".", exist_ok=True)
    fig.suptitle(
        f"FranksVals NP functions (postfit from {os.path.basename(args.from_fitresults)})",
        y=1.02,
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(args.outpath, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {args.outpath}")


if __name__ == "__main__":
    main()
