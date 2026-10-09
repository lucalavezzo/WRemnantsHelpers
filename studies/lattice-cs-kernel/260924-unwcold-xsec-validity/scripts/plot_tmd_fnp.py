"""f^NP(b_T, Y) = exp[-2 Linf b tanh B], B = L2(Y) b/Linf + (L4 + L2^3/(3 Linf^2)) b^3/Linf (tanh_2, Linf = 1),
L2(Y) = lambda2 + dlambda2 Y^2 (form: knowledge/30_physics_global/np_parametrization_constraints.md sec. 1, tanh_6 minus Lambda6).
Physical TMD lambdas of the three lattice-card fits (no alpha_s involved)."""

import argparse, os, sys
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_output import save_plot

p = argparse.ArgumentParser()
p.add_argument(
    "--outdir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
args = p.parse_args()
TUNES = {
    "LATL4ZUNWCOLD": (0.05213, -0.013276, -2.5e-5, "tab:red"),
    "LATL4ZUNWWARM": (-0.07835, -0.00949, 0.09561, "tab:purple"),
    "LATL4ZWALLCOLD": (0.02800, -0.00374, 0.08688, "tab:green"),
    "cache anchor": (0.4, 0.0, 0.4, "gray"),
}
b = np.linspace(1e-3, 12, 1200)


def fnp(l2, dl2, l4, Y, Li=1.0):
    L2 = l2 + dl2 * Y * Y
    B = L2 * b / Li + (l4 + L2**3 / (3 * Li**2)) * b**3 / Li
    return np.exp(-2 * Li * b * np.tanh(B))


fig, axs = plt.subplots(1, 2, figsize=(13, 5.2))
for ax, Y in zip(axs, [0.0, 2.5]):
    for k, (l2, dl2, l4, c) in TUNES.items():
        ax.plot(
            b,
            fnp(l2, dl2, l4, Y),
            color=c,
            label=f"{k}: L2={l2+dl2*Y*Y:+.3f}, $\\lambda_4$={l4:+.2g}",
        )
    ax.axhline(1, color="k", lw=0.5)
    ax.set_yscale("log")
    ax.set_ylim(1e-6, 1e4)
    ax.set_xlabel(r"$b_T$ (GeV$^{-1}$)", fontsize=14)
    ax.set_ylabel(r"$f^{\rm NP}(b_T, Y)$", fontsize=14)
    ax.set_title(f"TMD NP factor, tanh_2, $\\Lambda_\\infty$=1, |Y|={Y}", fontsize=13)
    ax.legend(fontsize=9, loc="lower left")
fig.tight_layout()
save_plot(
    args.outdir,
    "tmd_fnp_three_fits",
    fig=fig,
    args=args,
    meta_info={"tunes": {k: v[:3] for k, v in TUNES.items()}},
)
for k, (l2, dl2, l4, c) in TUNES.items():
    for Y in [0, 2.5]:
        f = fnp(l2, dl2, l4, Y)
        print(
            f"{k:15s} Y={Y}: max f {f.max():.3g} at b={b[f.argmax()]:.2f}, f(b=12)={f[-1]:.3g}"
        )
