"""T1: per-bin pull plots for all four projections.

Pull definition: r_i / sqrt(diag(cov_post)_ii + nobs_i)

The denominator uses the post-fit *prediction* covariance saved in
`hist_postfit_inclusive_cov` plus the per-bin Poisson term `nobs`.
This is an **approximation** of the residual covariance used in chi2
(see README findings); good enough for visual inspection of where the
postfit mismatch sits.

Usage:
    python per_bin_pulls.py <fitresults.hdf5> <out_dir>
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Make rabbit + wums importable from outside the container.
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult  # noqa: E402

PROJ_KEYS = [
    "Project ch0 ptll",
    "Project ch0 yll",
    "Project ch0 cosThetaStarll_quantile",
    "Project ch0 phiStarll_quantile",
]


def _hist_axis_centers(h):
    ax = h.axes[0]
    edges = ax.edges
    return 0.5 * (edges[:-1] + edges[1:]), edges


def make_pull_plot(fr, proj, out_dir):
    m = fr["mappings"][proj]
    chans = m["channels"]
    ch0 = chans["ch0"]
    data = ch0["hist_data_obs"].get().values()
    pred_post = ch0["hist_postfit_inclusive"].get().values()
    pred_pre = ch0["hist_prefit_inclusive"].get().values()
    nobs = ch0["hist_nobs"].get().values()
    if "hist_postfit_inclusive_cov" in m:
        cov_post = m["hist_postfit_inclusive_cov"].get().values()  # (N, N)
        diag_post = np.diag(cov_post)
    else:
        # Cov was not computed (no --computeHistCov). Use the variance of the
        # postfit prediction histogram as a fallback.
        h_pred = ch0["hist_postfit_inclusive"].get()
        try:
            diag_post = h_pred.variances()
        except Exception:
            diag_post = np.zeros_like(pred_post)

    res_post = pred_post - data
    res_pre = pred_pre - data
    sigma_post = np.sqrt(diag_post + nobs)
    pulls_post = res_post / sigma_post
    # Use the same denominator scale for prefit comparison (visual only).
    pulls_pre = res_pre / sigma_post

    centers, edges = _hist_axis_centers(ch0["hist_data_obs"].get())

    chi2_post = float(m["chi2"])
    ndf = float(m["ndf"])
    chi2_pre = float(m["chi2_prefit"]) if "chi2_prefit" in m else None
    chi2_sat = float(m["chi2_saturated"]) if "chi2_saturated" in m else None

    fig, axes = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]}
    )
    ax = axes[0]
    ax.errorbar(
        centers, data, yerr=np.sqrt(nobs), fmt="o", ms=3, color="k", label="data"
    )
    ax.step(
        edges, np.r_[pred_post[0], pred_post], where="pre", color="C0", label="postfit"
    )
    ax.step(
        edges,
        np.r_[pred_pre[0], pred_pre],
        where="pre",
        color="C3",
        label="prefit",
        alpha=0.7,
        ls="--",
    )
    ax.set_ylabel("Events / bin")
    title = f"{proj}: chi2/ndf = {chi2_post:.1f}/{ndf:.0f}"
    if chi2_pre is not None:
        title += f"  (prefit {chi2_pre:.1f})"
    if chi2_sat is not None:
        title += f"  (sat {chi2_sat:.1f})"
    ax.set_title(title)
    ax.legend(loc="best", fontsize=9)
    if pred_post.max() > 1e3:
        ax.set_yscale("log")

    ax2 = axes[1]
    width = np.diff(edges)
    ax2.bar(
        centers,
        pulls_post,
        width=width * 0.9,
        color="C0",
        alpha=0.85,
        label="postfit pull",
    )
    ax2.bar(
        centers,
        pulls_pre,
        width=width * 0.45,
        color="C3",
        alpha=0.55,
        label="prefit pull",
    )
    ax2.axhline(0, color="k", lw=0.5)
    for thr in (-2, -1, 1, 2):
        ax2.axhline(thr, color="grey", lw=0.4, ls=":")
    ax2.set_ylabel("(pred - data) / sigma")
    ax2.set_xlabel(proj)
    ax2.set_ylim(-3.5, 3.5)
    ax2.legend(loc="best", fontsize=8, ncol=2)

    fig.tight_layout()
    out_pdf = os.path.join(out_dir, f"per_bin_pulls_{proj}.pdf")
    out_png = os.path.join(out_dir, f"per_bin_pulls_{proj}.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)

    return {
        "proj": proj,
        "n_bins": len(data),
        "max_abs_pull_post": float(np.max(np.abs(pulls_post))),
        "argmax_pull_post": int(np.argmax(np.abs(pulls_post))),
        "max_abs_pull_pre": float(np.max(np.abs(pulls_pre))),
        "sum_chi2_post_approx": float(np.sum(pulls_post**2)),
        "sum_chi2_pre_approx": float(np.sum(pulls_pre**2)),
        "chi2_post_true": chi2_post,
        "chi2_pre_true": chi2_pre,
        "out_pdf": out_pdf,
    }


def main():
    fitres = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    fr, _ = get_fitresult(fitres, meta=True)
    rows = []
    for proj in PROJ_KEYS:
        if proj not in fr["mappings"]:
            print(f"Skipping {proj} (not in mappings)")
            continue
        rows.append(make_pull_plot(fr, proj, out_dir))
    print("\n=== T1 summary ===")
    print(f"input: {fitres}")
    print(f"out_dir: {out_dir}")
    for r in rows:
        print(
            f"  {r['proj']:30s} nbins={r['n_bins']:3d} "
            f"max|pull|_post={r['max_abs_pull_post']:.2f} (bin {r['argmax_pull_post']}) "
            f"max|pull|_pre={r['max_abs_pull_pre']:.2f} "
            f"sum_pull^2_post={r['sum_chi2_post_approx']:.1f} (true chi2 {r['chi2_post_true']:.1f}) "
            f"sum_pull^2_pre={r['sum_chi2_pre_approx']:.1f}"
        )


if __name__ == "__main__":
    main()
