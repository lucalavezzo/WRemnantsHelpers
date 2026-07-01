"""F10: muon-detector pull-vs-η scatter.

Maps effSyst_*_etaDecorr{K} (K=1..48) to η bin centers
(η edges: -2.4 + 0.1*i for i=0..48; bin K covers
[-2.4+(K-1)*0.1, -2.4+K*0.1]) and plots pull ± σ_post vs η bin center,
grouped by step (reco / tracking / iso / idip / trigger).

Prefire-region boundaries are not currently well-pinned from the saved
fitresults alone; I overlay |η| reference lines at standard CMS muon
boundaries (|η|=0.9 barrel, |η|=1.2 MB transition, |η|=1.6 ME ring,
|η|=2.1 endcap) for context. If the user has the actual prefire η-φ
region ranges, edit `PREFIRE_BOUNDARIES_ETA` below.

Output:
    out_dir/F10_pull_vs_eta_<tag>.{pdf,png}
    out_dir/F10_pull_vs_eta_<tag>.txt   (table of pulls per nuisance)

Usage:
    FITRES=... TAG=loose_NP python3 F10_pull_vs_eta.py [out_dir]
"""

import os
import re
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
from rabbit import io_tools  # noqa: E402

# η edges: -2.4 + 0.1*i for i in 0..48
ETA_EDGES = np.array([round(-2.4 + 0.1 * i, 1) for i in range(49)])
ETA_CENTERS = 0.5 * (ETA_EDGES[:-1] + ETA_EDGES[1:])

# Convention: effSyst_<step>_etaDecorr{K}, K=1..48 → bin index K-1 (η center
# at ETA_CENTERS[K-1]). K=0 (renamed "fullyCorr") is excluded — no η.

STEP_COLORS = {
    "reco": ("C0", "o"),
    "reco_altBkg": ("C0", "s"),
    "tracking": ("C1", "o"),
    "tracking_altBkg": ("C1", "s"),
    "idip": ("C2", "o"),
    "trigger": ("C3", "o"),
    "iso": ("C4", "o"),
    "veto": ("C5", "o"),
}

# Standard CMS muon boundaries — adjust if you have actual prefire regions.
PREFIRE_BOUNDARIES_ETA = [-2.1, -1.6, -1.2, -0.9, 0.9, 1.2, 1.6, 2.1]

# Regex to parse: effSyst_<step>(_altBkg)?_etaDecorr<K>
PARSE = re.compile(
    r"^effSyst_(?P<step>reco|tracking|idip|trigger|iso|veto)"
    r"(?P<alt>_altBkg)?_etaDecorr(?P<K>\d+)$"
)


def main():
    fitres_path = os.environ.get("FITRES")
    if fitres_path is None:
        raise SystemExit("set FITRES env var")
    tag = os.environ.get("TAG", "loose_NP")
    out_dir = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/home/submit/lavezzo/public_html/alphaS/F10_pull_vs_eta"
    )
    os.makedirs(out_dir, exist_ok=True)

    fr = io_tools.get_fitresult(fitres_path)
    labels, pulls, sigmas = io_tools.get_pulls_and_constraints(fr)
    labels = np.asarray(labels)
    pulls = np.asarray(pulls)
    sigmas = np.asarray(sigmas)

    rows = []
    for n, p, s in zip(labels, pulls, sigmas):
        m = PARSE.match(n)
        if not m:
            continue
        step = m.group("step")
        if m.group("alt"):
            step = step + "_altBkg"
        K = int(m.group("K"))
        if K < 1 or K > 48:
            continue
        eta = ETA_CENTERS[K - 1]
        rows.append((step, K, eta, float(p), float(s), n))

    if not rows:
        raise SystemExit("No effSyst_*_etaDecorr* nuisances found")

    # Optional: also pull the prefire entries to print
    prefire = []
    for n, p, s in zip(labels, pulls, sigmas):
        if "prefire_stat" in n:
            prefire.append((n, float(p), float(s)))

    # plot
    fig, axes = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ax = axes[0]
    seen_steps = set()
    for step, K, eta, p, s, n in rows:
        col, mk = STEP_COLORS.get(step, ("k", "x"))
        label = step if step not in seen_steps else None
        seen_steps.add(step)
        ax.errorbar(
            eta, p, yerr=s, fmt=mk, color=col, alpha=0.85, ms=6, capsize=2, label=label
        )
    ax.axhline(0, color="k", lw=0.5)
    for thr in (-2, -1, 1, 2):
        ax.axhline(thr, color="grey", lw=0.4, ls=":")
    for b in PREFIRE_BOUNDARIES_ETA:
        ax.axvline(b, color="grey", lw=0.4, ls="--", alpha=0.7)
    ax.set_ylabel(r"pull (postfit $\hat\theta$, prior $\sigma=1$)")
    ax.set_title(f"effSyst_*_etaDecorr pulls vs muon η — {tag}")
    ax.set_ylim(-3, 3)
    ax.legend(loc="best", ncol=4, fontsize=8)
    ax.set_xlim(-2.5, 2.5)

    # bottom panel: |pull| / sigma_post (tension significance)
    ax2 = axes[1]
    for step, K, eta, p, s, n in rows:
        col, mk = STEP_COLORS.get(step, ("k", "x"))
        if s > 0:
            ax2.scatter(eta, abs(p) / s, c=col, marker=mk, alpha=0.85, s=30)
    ax2.axhline(1, color="grey", lw=0.4, ls=":")
    ax2.axhline(2, color="grey", lw=0.4, ls=":")
    ax2.axhline(3, color="grey", lw=0.4, ls=":")
    for b in PREFIRE_BOUNDARIES_ETA:
        ax2.axvline(b, color="grey", lw=0.4, ls="--", alpha=0.7)
    ax2.set_xlabel(r"muon $\eta$ (bin center)")
    ax2.set_ylabel(r"|pull| / $\sigma_\mathrm{post}$ (tension)")
    ax2.set_ylim(0, 5)

    fig.tight_layout()
    out_pdf = os.path.join(out_dir, f"F10_pull_vs_eta_{tag}.pdf")
    out_png = os.path.join(out_dir, f"F10_pull_vs_eta_{tag}.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"Saved: {out_pdf}")

    # text dump
    out_txt = os.path.join(out_dir, f"F10_pull_vs_eta_{tag}.txt")
    rows_sorted = sorted(rows, key=lambda r: -abs(r[3]))
    with open(out_txt, "w") as f:
        f.write(f"# pull-vs-η table for effSyst_*_etaDecorr* in {fitres_path}\n")
        f.write(f"# tag = {tag}\n#\n")
        f.write(
            f"# {'step':20s}{'K':>3}{'eta':>7}{'pull':>9}{'σ_post':>9}{'tension':>8}  name\n"
        )
        for step, K, eta, p, s, n in rows_sorted:
            tens = abs(p) / s if s > 0 else 0
            f.write(
                f"  {step:20s}{K:>3}{eta:>7.2f}{p:>+9.3f}{s:>9.3f}{tens:>8.2f}  {n}\n"
            )
        f.write("\n# Prefire stat nuisances (no η-bin mapping yet):\n")
        for n, p, s in sorted(prefire, key=lambda r: -abs(r[1])):
            tens = abs(p) / s if s > 0 else 0
            f.write(f"  {n:50s}{'':>3}{'':>7}{p:>+9.3f}{s:>9.3f}{tens:>8.2f}\n")
    print(f"Saved: {out_txt}")

    # quick summary
    n_high = sum(1 for r in rows if abs(r[3]) > 1.0)
    n_2sig = sum(1 for r in rows if abs(r[3]) > 2.0)
    n_total = len(rows)
    sumpull2 = sum(r[3] ** 2 for r in rows)
    print(f"\n{n_total} effSyst_*_etaDecorr* nuisances total")
    print(f"  {n_high} with |pull| > 1.0  ({100*n_high/n_total:.0f}%)")
    print(f"  {n_2sig} with |pull| > 2.0  ({100*n_2sig/n_total:.0f}%)")
    print(f"  Σ pull² over all = {sumpull2:.2f}")
    print(
        f"  (random-Gaussian-of-1 expectation: ~{n_total} for Σpull², "
        f"~{n_total*0.32:.0f} above |1|σ, ~{n_total*0.046:.0f} above |2|σ)"
    )


if __name__ == "__main__":
    main()
