"""T2: 2D residual heatmap on (ptll, yll) for the 4D fit including
`-m Project ch0 ptll yll`.

Reads the 2D mapping's saved hists and plots
   z = (pred_post - data) / sqrt(diag(cov_post) + nobs)        (bins, sigma)
   z = (pred_post - data) / sqrt(nobs)                         (data-only sigma fallback)

If hist_postfit_inclusive_cov is missing for the 2D mapping, fall back to
sqrt(nobs) and note that in the title.

Usage:
    python residual_2d_heatmap.py <fitresults.hdf5> <out_dir>
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult  # noqa: E402

KEY = "Project ch0 ptll yll"


def main():
    fitres = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    fr, _ = get_fitresult(fitres, meta=True)
    if KEY not in fr["mappings"]:
        print(
            f"ERROR: mapping '{KEY}' not in fitresults; available: "
            f"{list(fr['mappings'])}"
        )
        sys.exit(1)
    m = fr["mappings"][KEY]
    ch0 = m["channels"]["ch0"]
    h_data = ch0["hist_data_obs"].get()
    h_pred = ch0["hist_postfit_inclusive"].get()
    nobs = ch0["hist_nobs"].get().values()
    data = h_data.values()
    pred = h_pred.values()
    res = pred - data

    cov_label = "diag(cov_post)+nobs"
    if "hist_postfit_inclusive_cov" in m:
        cov = m["hist_postfit_inclusive_cov"].get().values()
        diag = np.diag(cov).reshape(data.shape)
        sigma = np.sqrt(diag + nobs)
    else:
        try:
            diag = h_pred.variances()
            sigma = np.sqrt(diag + nobs)
            cov_label = "sqrt(var_pred + nobs) [no full cov saved]"
        except Exception:
            sigma = np.sqrt(nobs)
            cov_label = "sqrt(nobs) [no cov / variance available]"

    pulls = res / sigma

    # Axes for plotting.
    ax_ptll = h_data.axes[0]
    ax_yll = h_data.axes[1]
    edges_pt = ax_ptll.edges
    edges_y = ax_yll.edges

    chi2_post = float(m["chi2"])
    ndf = float(m["ndf"])
    chi2_pre = float(m.get("chi2_prefit", float("nan")))
    chi2_sat = float(m.get("chi2_saturated", float("nan")))

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    extent = [edges_y[0], edges_y[-1], edges_pt[0], edges_pt[-1]]
    norm = TwoSlopeNorm(vmin=-3.5, vcenter=0, vmax=3.5)
    im0 = axes[0].imshow(
        pulls, origin="lower", aspect="auto", extent=extent, cmap="RdBu_r", norm=norm
    )
    axes[0].set_xlabel(ax_yll.name)
    axes[0].set_ylabel(ax_ptll.name)
    axes[0].set_title(
        f"postfit pull (pred-data)/{cov_label}\n"
        f"chi2/ndf = {chi2_post:.1f}/{ndf:.0f}  prefit {chi2_pre:.1f}  sat {chi2_sat:.1f}"
    )
    plt.colorbar(im0, ax=axes[0])

    im1 = axes[1].imshow(
        pred, origin="lower", aspect="auto", extent=extent, cmap="viridis"
    )
    axes[1].set_xlabel(ax_yll.name)
    axes[1].set_ylabel(ax_ptll.name)
    axes[1].set_title("postfit prediction (events)")
    plt.colorbar(im1, ax=axes[1])

    im2 = axes[2].imshow(
        res,
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap="RdBu_r",
        norm=TwoSlopeNorm(
            vmin=-np.max(np.abs(res)), vcenter=0, vmax=np.max(np.abs(res))
        ),
    )
    axes[2].set_xlabel(ax_yll.name)
    axes[2].set_ylabel(ax_ptll.name)
    axes[2].set_title("postfit residual pred-data (events)")
    plt.colorbar(im2, ax=axes[2])

    fig.tight_layout()
    out = os.path.join(out_dir, "residual_2d_ptll_yll.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=120)
    plt.close(fig)
    print(f"Saved: {out}")

    # Numerical diagnostics: which bins have |pull|>2?
    flat = pulls.flatten()
    big = np.where(np.abs(flat) > 2)[0]
    print(f"|pull|>2 bins: {len(big)} of {flat.size}")
    iy = ax_yll.size
    for i in big[:20]:
        ipt, iy_ = divmod(i, iy)
        print(
            f"  pull={flat[i]:+.2f}  ptll bin {ipt} ({edges_pt[ipt]:.1f}-{edges_pt[ipt+1]:.1f}), "
            f"yll bin {iy_} ({edges_y[iy_]:.2f}-{edges_y[iy_+1]:.2f})"
        )
    print(f"sum pull^2 = {(pulls**2).sum():.1f}  (true chi2 {chi2_post:.1f})")


if __name__ == "__main__":
    main()
