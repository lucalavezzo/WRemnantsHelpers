"""Plot the np_monotonicity regularizer wall penalty 1D, scanning each of
the six NP parameters with the others frozen at AN central values. This
exposes (per parameter) where the wall starts firing and how steep it is.

Walls (criterion b, default; signature must match np_monotonicity.py:
  cs_l2_pos_pen      = max(0, -λ_2)²                     (λ_2 ≥ 0)
  cs_pen             = max(0, cs_floor - λ_4)²
                       where cs_floor = -√(3·max(λ_2,0)·λ_6)
  tmd_L2_pos_pen(y)  = max(0, -L_2(y))²                  (L_2(y) ≥ 0)
  tmd_c1_pen(y)      = max(0, tmd_floor(y) - c_1(y))²
                       where tmd_floor(y) = -√(20·Λ_6·max(L_2(y),0))
                             c_1(y)       = 3·Λ_4 + max(L_2(y),0)³
                             L_2(y)       = Λ_2 + Δ_Λ_2·y²
TMD walls are summed at y=0 and y=Y_MAX.

The total penalty plotted is the bare sum P (before the exp(2τ) multiplier).
Where 2·τ = 10 (the configs we run), the actual NLL contribution is P·22 026.
"""

import argparse, os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Constants (must match np_monotonicity.py)
LAMBDA_6 = 0.0007  # CS
BIG_LAMBDA_6 = 0.016  # TMD
Y_MAX = 2.5
K_CS = 3.0  # criterion b
K_TMD = 20.0  # criterion b

# AN central (the freeze point for "others")
AN = dict(
    lambda_2=0.0870,
    lambda_4=0.0074,
    lambda_inf=1.6853,
    Lambda_2=0.25,
    Delta_Lambda_2=0.0,
    Lambda_4=0.06,
)
# Note: Delta_Lambda_2 nominal in the LatticeNoConstraints lowercase branch is 0
# (templates at ±0.02 absolute); the AN "0.125" applies to a different branch.


def constraint_funcs(p):
    """Return a dict {name: f(p)} where each f is the constraint function whose
    wall is f ≥ 0 (i.e. f > 0 → safe, f < 0 → violated).

    The penalty per constraint is max(0, -f)². Plotting f directly shows the
    margin to / past the wall on every active constraint.
    """
    l2 = p["lambda_2"]
    l4 = p["lambda_4"]
    L2 = p["Lambda_2"]
    DL2 = p["Delta_Lambda_2"]
    L4 = p["Lambda_4"]
    l2_safe = max(l2, 0.0)
    cs_floor = -np.sqrt(K_CS * l2_safe * LAMBDA_6)
    out = {
        r"$\lambda_2$": l2,
        r"$\lambda_4 - \mathrm{floor}_{\rm CS}$": l4 - cs_floor,
    }
    for y, y_sq, ylab in ((0.0, 0.0, "0"), (Y_MAX, Y_MAX**2, str(Y_MAX))):
        L2y = L2 + DL2 * y_sq
        L2y_safe = max(L2y, 0.0)
        c1 = 3.0 * L4 + L2y_safe**3
        floor = -np.sqrt(K_TMD * BIG_LAMBDA_6 * L2y_safe)
        out[rf"$L_2(y{{=}}{ylab})$"] = L2y
        out[rf"$c_1(y{{=}}{ylab}) - \mathrm{{floor}}_{{\rm TMD}}(y{{=}}{ylab})$"] = (
            c1 - floor
        )
    return out


def wall_penalty(p):
    """Total penalty: sum of max(0, -f)² over all constraints in constraint_funcs."""
    return sum(max(0.0, -f) ** 2 for f in constraint_funcs(p).values())


# Constraints that respond to each scanned parameter (used to thin the
# constraint-function panels to the ones that actually vary).
ACTIVE_CONSTRAINTS = {
    "lambda_2": [r"$\lambda_2$", r"$\lambda_4 - \mathrm{floor}_{\rm CS}$"],
    "lambda_4": [r"$\lambda_4 - \mathrm{floor}_{\rm CS}$"],
    "Lambda_2": [
        r"$L_2(y{=}0)$",
        rf"$L_2(y{{=}}{Y_MAX})$",
        r"$c_1(y{=}0) - \mathrm{floor}_{\rm TMD}(y{=}0)$",
        rf"$c_1(y{{=}}{Y_MAX}) - \mathrm{{floor}}_{{\rm TMD}}(y{{=}}{Y_MAX})$",
    ],
    "Delta_Lambda_2": [
        r"$L_2(y{=}0)$",
        rf"$L_2(y{{=}}{Y_MAX})$",
        r"$c_1(y{=}0) - \mathrm{floor}_{\rm TMD}(y{=}0)$",
        rf"$c_1(y{{=}}{Y_MAX}) - \mathrm{{floor}}_{{\rm TMD}}(y{{=}}{Y_MAX})$",
    ],
    "Lambda_4": [
        r"$c_1(y{=}0) - \mathrm{floor}_{\rm TMD}(y{=}0)$",
        rf"$c_1(y{{=}}{Y_MAX}) - \mathrm{{floor}}_{{\rm TMD}}(y{{=}}{Y_MAX})$",
    ],
}


# Predefined postfit points to over-plot
POSTFIT = {
    "AN central": AN,
    "inflate2x": dict(
        lambda_2=-0.1977,
        lambda_4=+0.0157,
        lambda_inf=+1.8244,
        Lambda_2=+0.6856,
        Delta_Lambda_2=-0.0149,
        Lambda_4=-0.0222,
    ),
    "inflate5x": dict(
        lambda_2=-0.5407,
        lambda_4=+0.0673,
        lambda_inf=+1.8102,
        Lambda_2=+1.4149,
        Delta_Lambda_2=-0.0151,
        Lambda_4=-0.0392,
    ),
    "unconstrained τ=3": dict(
        lambda_2=-0.0346,
        lambda_4=+0.0291,
        lambda_inf=1.6853,
        Lambda_2=+0.3568,
        Delta_Lambda_2=-0.0137,
        Lambda_4=-0.1076,
    ),
}

# Scan range per parameter (centered loosely on AN where useful)
# Constraint expressions written directly in the underlying NP parameters
# (no L_2(y), c_1(y) shorthand). y_m ≡ y_max = 2.5, so y_m² = 6.25.
SCANS = [
    (
        "lambda_2",
        np.linspace(-0.8, 0.8, 401),
        r"$\lambda_2$",
        "CS",
        r"$\lambda_2 \geq 0$" "\n" r"$\lambda_4 \geq -\sqrt{3\,\lambda_2\,\lambda_6}$",
    ),
    (
        "lambda_4",
        np.linspace(-0.10, 0.10, 401),
        r"$\lambda_4$",
        "CS",
        r"$\lambda_4 \geq -\sqrt{3\,\lambda_2\,\lambda_6}$",
    ),
    (
        "Lambda_2",
        np.linspace(-0.5, 2.0, 401),
        r"$\Lambda_2$",
        "TMD",
        r"$\Lambda_2 \geq 0$"
        "\n"
        r"$\Lambda_2 + 6.25\,\Delta\Lambda_2 \geq 0$"
        "\n"
        r"$3\Lambda_4 + \Lambda_2^3 \geq -\sqrt{20\,\Lambda_6\,\Lambda_2}$"
        "\n"
        r"$3\Lambda_4 + (\Lambda_2{+}6.25\Delta\Lambda_2)^3 \geq -\sqrt{20\,\Lambda_6\,(\Lambda_2{+}6.25\Delta\Lambda_2)}$",
    ),
    (
        "Delta_Lambda_2",
        np.linspace(-0.5, 0.5, 401),
        r"$\Delta\Lambda_2$",
        "TMD",
        r"$\Lambda_2 + 6.25\,\Delta\Lambda_2 \geq 0$"
        "\n"
        r"$3\Lambda_4 + (\Lambda_2{+}6.25\Delta\Lambda_2)^3 \geq -\sqrt{20\,\Lambda_6\,(\Lambda_2{+}6.25\Delta\Lambda_2)}$",
    ),
    (
        "Lambda_4",
        np.linspace(-1.5, 0.5, 401),
        r"$\Lambda_4$",
        "TMD",
        r"$3\Lambda_4 + \Lambda_2^3 \geq -\sqrt{20\,\Lambda_6\,\Lambda_2}$"
        "\n"
        r"$3\Lambda_4 + (\Lambda_2{+}6.25\Delta\Lambda_2)^3 \geq -\sqrt{20\,\Lambda_6\,(\Lambda_2{+}6.25\Delta\Lambda_2)}$",
    ),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", "-o", required=True)
    args = p.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    n = len(SCANS)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axes = [axes]

    postfit_colors = {"inflate2x": "C1", "inflate5x": "C3", "unconstrained τ=3": "C2"}

    for ax, (pname, xs, label, side, constraint_text) in zip(axes, SCANS):
        ys_P = [wall_penalty({**AN, pname: x}) for x in xs]
        ax.plot(xs, ys_P, color="C0", lw=2, label=r"penalty $P$")
        ax.axvline(
            AN[pname],
            color="grey",
            ls=":",
            lw=1,
            alpha=0.7,
            label=f"AN = {AN[pname]:.4f}",
        )
        for plab, pdct in POSTFIT.items():
            if plab == "AN central":
                continue
            xv = pdct[pname]
            yv = wall_penalty({**AN, pname: xv})
            ax.scatter(
                [xv],
                [yv],
                color=postfit_colors[plab],
                s=40,
                zorder=5,
                label=f"{plab}: {xv:+.3f}",
            )
        ax.set_xlabel(label)
        ax.set_ylabel(r"$P = \sum_i \max(0,-f_i)^2$")
        ax.set_title(f"{side}: scan {label}, others frozen at AN")
        ax.legend(loc="best", fontsize=7)
        ax.grid(alpha=0.3)
        # Constraint expression(s) as a text box in the upper-left.
        ax.text(
            0.03,
            0.97,
            constraint_text,
            transform=ax.transAxes,
            fontsize=9,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.6", alpha=0.85),
        )

    fig.suptitle(
        "Squared-hinge wall penalty $P(\\lambda) = \\sum_i \\max(0, -f_i)^2$ "
        "(others frozen at AN central; criterion b)",
        fontsize=11,
    )
    fig.tight_layout()
    out = os.path.join(args.outdir, "wall_penalty_1d.png")
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
