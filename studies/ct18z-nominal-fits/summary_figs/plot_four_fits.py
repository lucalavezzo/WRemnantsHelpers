"""Four-fit comparison for the SUMMARY: blinded alpha_s differences and sigma(alpha_s).

Reads only ct18z-nominal-fits/261017-gen-cold-fits/compare.json (no fits, no caches).
x = alpha_s(fit) - alpha_s(RECO_NOLAT) in units of 1e-3 (blinded difference, same blinding frame);
error bar = that fit's OWN face-held sigma(alpha_s), not the uncertainty of the difference.
"""

import json
import os
import sys

from wums import plot_tools  # noqa: F401  (import at top: applies the CMS style)
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "261015-trustconstr-warmstart"))
from plot_output import save_plot  # noqa: E402

src = os.path.join(HERE, "..", "261017-gen-cold-fits", "compare.json")
d = json.load(open(src))
dif = d["alphaS_differences"]
sig = {k: v["sigma_alphaS_1e3"] for k, v in d["fits"].items()}
x = {
    "RECO_NOLAT": 0.0,
    "RECO_LAT": dif["RECO_LAT - RECO_NOLAT"]["alpha_s"] * 1e3,
    "GEN_NOLAT": dif["GEN_NOLAT - RECO_NOLAT"]["alpha_s"] * 1e3,
}
x["GEN_LAT"] = x["GEN_NOLAT"] + dif["GEN_LAT - GEN_NOLAT"]["alpha_s"] * 1e3
alt = x["RECO_LAT"] + dif["GEN_LAT - RECO_LAT"]["alpha_s"] * 1e3
assert abs(alt - x["GEN_LAT"]) < 1e-9

order = ["RECO_NOLAT", "RECO_LAT", "GEN_NOLAT", "GEN_LAT"]
labels = {
    "RECO_NOLAT": "reco, Z only",
    "RECO_LAT": "reco, Z + lattice",
    "GEN_NOLAT": "gen (unfolded), Z only",
    "GEN_LAT": "gen (unfolded), Z + lattice",
}
cols = {
    "RECO_NOLAT": "#5790fc",
    "RECO_LAT": "#964a8b",
    "GEN_NOLAT": "#f89c20",
    "GEN_LAT": "#e42536",
}

fig, ax = plt.subplots(figsize=(7.5, 4.2))
for i, k in enumerate(order[::-1]):
    ax.errorbar(x[k], i, xerr=sig[k], fmt="o", color=cols[k], ms=8, capsize=4, lw=2)
    ax.text(
        x[k],
        i + 0.22,
        f"{x[k]:+.2f} ± {sig[k]:.2f}",
        ha="center",
        va="bottom",
        fontsize=13,
    )
ax.axvline(0, color="gray", ls="--", lw=1)
ax.set_yticks(range(4))
ax.set_yticklabels([labels[k] for k in order[::-1]], fontsize=14)
ax.set_ylim(-0.6, 3.8)
ax.set_xlabel(
    r"$\alpha_\mathrm{s} - \alpha_\mathrm{s}^\mathrm{reco,\,Z\ only}$  [$10^{-3}$]  (blinded)",
    fontsize=15,
)
ax.tick_params(axis="x", labelsize=13)
ax.set_xlim(-2.1, 1.7)
fig.tight_layout()
save_plot(HERE, "four_fits_alphas", fig=fig, meta_info={"source": src})
print({k: (round(x[k], 4), round(sig[k], 4)) for k in order})
