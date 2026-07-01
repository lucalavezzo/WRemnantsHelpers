"""Plot the SCETlib NP CS kernel and TMD boundary condition for a chosen
set of 6 NP parameters, alongside the AN-25-085 central values for reference.

Functional forms (AN-25-085 eqs. eq:npgamma / eq:npf, plus our locally added
λ_6 / Λ_6 b_T-tail coefficients — see
knowledge/30_physics_global/np_parametrization_constraints.md):

    γ̃^NP(b_T)   = −(λ_∞/2) · tanh A(b_T)
    A(b_T)·λ_∞  = λ_2 b_T² + λ_4 b_T⁴ + λ_6 b_T⁶

    f^NP(b_T,y) = exp[ −2 Λ_∞ b_T · tanh B(b_T,y) ]
    B(b_T,y)·Λ_∞ = L_2(y) b_T + (c_1(y)/3) b_T³ + Λ_6 b_T⁵
                  with L_2(y) = Λ_2 + Δ_Λ_2 y²,  c_1(y) = 3 Λ_4 + L_2(y)³

Fixed constants:  λ_6 = 0.0007,  Λ_6 = 0.016,  Λ_∞ (TMD) = 1.0.
"""

import argparse, os, json, sys
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

LAMBDA_6_CS = 0.0007  # CS, fixed (default; --lambda_6 overrides)
LAMBDA_6_TMD = 0.016  # TMD, fixed (default; --Lambda_6 overrides)
LAMBDA_INF_TMD = 1.0  # TMD, fixed (default; --Lambda_inf overrides)

AN = dict(
    lambda_2=0.0870,
    lambda_4=0.0074,
    lambda_inf=1.6853,
    Lambda_2=0.25,
    Delta_Lambda_2=0.0,
    Lambda_4=0.06,
)


def gamma_NP(bT, p):
    A_times_linf = p["lambda_2"] * bT**2 + p["lambda_4"] * bT**4 + LAMBDA_6_CS * bT**6
    A = A_times_linf / p["lambda_inf"]
    return -0.5 * p["lambda_inf"] * np.tanh(A)


def f_NP(bT, y, p):
    L2y = p["Lambda_2"] + p["Delta_Lambda_2"] * y**2
    c1y = 3.0 * p["Lambda_4"] + L2y**3
    B_times_Linf = L2y * bT + (c1y / 3.0) * bT**3 + LAMBDA_6_TMD * bT**5
    B = B_times_Linf / LAMBDA_INF_TMD
    return np.exp(-2.0 * LAMBDA_INF_TMD * bT * np.tanh(B))


# --- Postfit-from-fitresults toy propagation ---------------------------------
NP_NUIS = [
    "scetlibNPgammaLambda2",  # → CS λ_2
    "scetlibNPgammaLambda4",  # → CS λ_4
    "scetlibNPgammaLambdaInf",  # → CS λ_∞
    "chargeVgenNP0scetlibNPZlambda2",  # → TMD Λ_2
    "chargeVgenNP0scetlibNPZdelta_lambda2",  # → TMD Δ_Λ_2
    "chargeVgenNP0scetlibNPZlambda4",  # → TMD Λ_4
]
NP_PHYS_KEY = [
    "lambda_2",
    "lambda_4",
    "lambda_inf",
    "Lambda_2",
    "Delta_Lambda_2",
    "Lambda_4",
]


def _theta_to_physical(theta, nuis, kfactor):
    """Piecewise linearization (matches np_monotonicity.py and build_compare_table.py)."""
    pmap_path = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/np_param_map.json"
    with open(pmap_path) as f:
        pmap = json.load(f)["nuisances"][nuis]
    nom = pmap["nominal"]
    d_up = (pmap["Up_template_value"] - nom) * kfactor
    d_dn = (nom - pmap["Down_template_value"]) * kfactor
    return nom + np.maximum(theta, 0) * d_up - np.maximum(-theta, 0) * d_dn


def sample_toys(fitresults_path, kfactors, n_toys, seed=0):
    """Read postfit means+cov for the 6 NPs, sample n_toys θ-vectors from MVN,
    translate each to physical {lambda_2, lambda_4, ..., Lambda_4}.

    Returns (central_dict, toys_phys) where central_dict is the postfit
    physical point and toys_phys is a list of dicts (one per toy).
    Frozen parameters (variance 0 in cov) are kept at their central value.
    """
    sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
    sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
    from rabbit.io_tools import get_fitresult

    fr, _ = get_fitresult(fitresults_path, meta=True)
    parms = fr["parms"].get()
    names = list(parms.axes[0])
    cov_h = fr["cov"].get()
    cov_names = list(cov_h.axes[0])
    cov = cov_h.values()

    # Pull θ and variance for each NP; identify frozen.
    theta = np.zeros(len(NP_NUIS))
    in_cov = [False] * len(NP_NUIS)
    cov_idx = []
    for k, nm in enumerate(NP_NUIS):
        if nm in names:
            theta[k] = float(parms.values()[names.index(nm)])
        # Frozen params are typically absent from cov OR have variance 0.
        if nm in cov_names:
            ci = cov_names.index(nm)
            if cov[ci, ci] > 0:
                in_cov[k] = True
                cov_idx.append((k, ci))

    def _kf(k):
        # Accept kfactor keyed by either the rabbit nuisance name or the
        # physical-parameter name (whichever the user passed).
        return kfactors.get(NP_NUIS[k], kfactors.get(NP_PHYS_KEY[k], 1.0))

    central_phys = {
        NP_PHYS_KEY[k]: float(_theta_to_physical(theta[k], NP_NUIS[k], _kf(k)))
        for k in range(len(NP_NUIS))
    }

    # Sample θ-toys only for unfrozen params, then expand back to 6-vec.
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
        d = {}
        for k in range(len(NP_NUIS)):
            d[NP_PHYS_KEY[k]] = float(
                _theta_to_physical(toys_theta[t, k], NP_NUIS[k], _kf(k))
            )
        toys_phys.append(d)
    return central_phys, toys_phys


def parse_kfactor_args(args):
    out = {}
    if not args:
        return out
    for tok in args:
        k, v = tok.split("=", 1)
        out[k] = float(v)
    return out


# -----------------------------------------------------------------------------


def main():
    # Declared up-front because we may overwrite the module-level
    # higher-order coefficients below.
    global LAMBDA_6_CS, LAMBDA_6_TMD, LAMBDA_INF_TMD

    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # Direct CLI mode (no uncertainties)
    p.add_argument("--lambda_2", type=float)
    p.add_argument("--lambda_4", type=float)
    p.add_argument("--lambda_inf", type=float)
    p.add_argument("--Lambda_2", type=float)
    p.add_argument("--Delta_Lambda_2", type=float)
    p.add_argument("--Lambda_4", type=float)
    # Postfit-from-fitresults mode (with uncertainty band)
    p.add_argument(
        "--from-fitresults", help="Path to fitresults.hdf5 to read postfit + cov from"
    )
    p.add_argument(
        "--kfactor",
        nargs="*",
        default=[],
        help="Per-NP kfactor overrides as NAME=K (e.g. lambda_2=2.62). "
        "Apply this when the workspace was built with --scaleParams.",
    )
    p.add_argument(
        "--n-toys",
        type=int,
        default=500,
        help="Number of toys to sample from postfit MVN (default 500)",
    )
    # Common
    p.add_argument("--label", default="postfit")
    p.add_argument("--y", type=float, nargs="+", default=[0.0, 2.5])
    p.add_argument("--bT-max", type=float, default=4.0)
    p.add_argument("--outpath", "-o", required=True)
    # Override fixed higher-order coefficients (default AN values)
    p.add_argument(
        "--lambda_6",
        type=float,
        default=None,
        help=f"Override CS lambda_6 (default {LAMBDA_6_CS})",
    )
    p.add_argument(
        "--Lambda_6",
        type=float,
        default=None,
        help=f"Override TMD Lambda_6 (default {LAMBDA_6_TMD})",
    )
    p.add_argument(
        "--Lambda_inf",
        type=float,
        default=None,
        help=f"Override TMD Lambda_inf (default {LAMBDA_INF_TMD})",
    )
    args = p.parse_args()

    # Apply higher-order coefficient overrides (mutates module globals so
    # gamma_NP/f_NP pick them up).
    if args.lambda_6 is not None:
        LAMBDA_6_CS = args.lambda_6
    if args.Lambda_6 is not None:
        LAMBDA_6_TMD = args.Lambda_6
    if args.Lambda_inf is not None:
        LAMBDA_INF_TMD = args.Lambda_inf

    toys = None
    if args.from_fitresults:
        kfactors = parse_kfactor_args(args.kfactor)
        point, toys = sample_toys(args.from_fitresults, kfactors, args.n_toys)
        print(f"Loaded postfit from {args.from_fitresults}")
        for k, v in point.items():
            print(f"  {k:<18s} = {v:+.4f}")
    else:
        required = [
            args.lambda_2,
            args.lambda_4,
            args.lambda_inf,
            args.Lambda_2,
            args.Delta_Lambda_2,
            args.Lambda_4,
        ]
        if any(v is None for v in required):
            raise SystemExit(
                "Either pass --from-fitresults or all six --lambda_*/--Lambda_* values."
            )
        point = dict(
            lambda_2=args.lambda_2,
            lambda_4=args.lambda_4,
            lambda_inf=args.lambda_inf,
            Lambda_2=args.Lambda_2,
            Delta_Lambda_2=args.Delta_Lambda_2,
            Lambda_4=args.Lambda_4,
        )

    bT = np.linspace(0, args.bT_max, 401)
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 4.5))

    # If we have toys, compute 16/84 percentile bands on γ̃^NP(b_T) and on f^NP(b_T,y) per y.
    band_cs = None
    band_tmd = {}  # y → (lo, hi)
    if toys is not None:
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

    # Left panel: CS kernel γ̃^NP(b_T)
    axL.plot(bT, gamma_NP(bT, AN), label="AN central", color="C0", lw=2)
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
        -0.5 * AN["lambda_inf"],
        color="C0",
        ls=":",
        lw=1,
        label=rf"AN asymptote $-\lambda_\infty/2$ = {-0.5*AN['lambda_inf']:.3f}",
    )
    axL.set_xlabel(r"$b_T$ [GeV$^{-1}$]")
    axL.set_ylabel(r"$\tilde\gamma^{\rm NP}(b_T)$")
    axL.set_title(
        r"$\tilde\gamma^{\rm NP}(b_T) = -\frac{\lambda_\infty}{2}\,"
        r"\tanh[\,(\lambda_2 b_T^2 + \lambda_4 b_T^4 + \lambda_6 b_T^6)/\lambda_\infty\,]$",
        fontsize=10,
    )
    axL.legend(loc="lower left", fontsize=9)
    axL.grid(alpha=0.3)

    # Right panel: TMD f^NP(b_T, y)
    cmap_AN = plt.cm.Blues
    cmap_P = plt.cm.Reds
    n = len(args.y)
    for i, y in enumerate(args.y):
        shade = 0.4 + 0.5 * (i / max(n - 1, 1))
        axR.plot(
            bT, f_NP(bT, y, AN), color=cmap_AN(shade), lw=2, label=f"AN central, y={y}"
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
        r"$f^{\rm NP}(b_T,y) = \exp[\,-2\,\Lambda_\infty\,b_T\,"
        r"\tanh(\,[(\Lambda_2{+}\Delta\Lambda_2\,y^2) b_T + \Lambda_4 b_T^3 + "
        r"\frac{(\Lambda_2{+}\Delta\Lambda_2\,y^2)^3}{3} b_T^3 + \Lambda_6 b_T^5\,]\,/\,\Lambda_\infty\,)\,]$",
        fontsize=9,
    )
    axR.legend(loc="center right", fontsize=8)
    axR.grid(alpha=0.3)

    # Parameter inset per panel: CS params on the left, TMD params on the right.
    box = dict(boxstyle="round,pad=0.35", fc="white", ec="0.6", alpha=0.85)
    cs_text = (
        f"$\\lambda_2 = {point['lambda_2']:+.4f}$\n"
        f"$\\lambda_4 = {point['lambda_4']:+.4f}$\n"
        f"$\\lambda_\\infty = {point['lambda_inf']:+.4f}$\n"
        f"$\\lambda_6 = {LAMBDA_6_CS}$ (fixed)"
    )
    tmd_text = (
        f"$\\Lambda_2 = {point['Lambda_2']:+.4f}$\n"
        f"$\\Delta\\Lambda_2 = {point['Delta_Lambda_2']:+.4f}$\n"
        f"$\\Lambda_4 = {point['Lambda_4']:+.4f}$\n"
        f"$\\Lambda_6 = {LAMBDA_6_TMD}$ (fixed)\n"
        f"$\\Lambda_\\infty = {LAMBDA_INF_TMD}$ (fixed)"
    )
    # CS panel: curves go from (0,0) down to negative asymptote → upper-right
    # is always empty. TMD panel: curves start near 1 and decay → bottom-left
    # below the curves is usually empty across configs. Legend on the TMD
    # panel moves to lower-right to avoid colliding with the param box.
    axL.text(
        0.97,
        0.97,
        cs_text,
        transform=axL.transAxes,
        fontsize=8,
        va="top",
        ha="right",
        bbox=box,
    )
    axR.text(
        0.97,
        0.97,
        tmd_text,
        transform=axR.transAxes,
        fontsize=8,
        va="top",
        ha="right",
        bbox=box,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.outpath)) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(args.outpath, dpi=140)
    plt.close(fig)
    print(f"Wrote {args.outpath}")


if __name__ == "__main__":
    main()
