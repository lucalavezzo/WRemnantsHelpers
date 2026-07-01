"""T11/T16: residual anatomy on a 1D projection.

Decomposes (data - model) on a chosen projection into three parts:

    1. r_pre   = pred_pre  - data    (initial mismatch)
    2. r_post  = pred_post - data    (mismatch left after nuisances pulled)
    3. dpred   = pred_post - pred_pre = -(r_pre - r_post)
       (the shape the nuisances added to pull the model toward the data)

Then eigendecomposes the residual covariance
    C  =  cov_post  +  diag(nobs)
and reports the chi2 contribution of each mode as
    chi2_k  =  (u_k . r_post)^2 / lambda_k
where (lambda_k, u_k) are eigenpairs of C, sorted by chi2 contribution.

Caveat: this C is the postfit-prediction-cov approximation, which under-
counts the true rabbit chi2 by ~2x in absolute terms (per the
projection_pvalues README and T3). The *ranking* of modes is robust.

Usage:
    python residual_anatomy.py <fitresults.hdf5> <out_dir> [proj_key]

Output:
    out_dir/anatomy_<proj>.{pdf,png}      4-panel residual anatomy
    out_dir/eigenmodes_<proj>.{pdf,png}   top eigenmodes of residual cov
    out_dir/eigen_table_<proj>.txt        per-mode chi2 table
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult  # noqa: E402


def hist_axis(ch0, name="hist_data_obs"):
    h = ch0[name].get()
    edges = h.axes[0].edges
    centers = 0.5 * (edges[:-1] + edges[1:])
    return centers, edges


def load_proj(fr, proj):
    m = fr["mappings"][proj]
    ch0 = m["channels"]["ch0"]
    data = ch0["hist_data_obs"].get().values()
    pred_post = ch0["hist_postfit_inclusive"].get().values()
    pred_pre = ch0["hist_prefit_inclusive"].get().values()
    nobs = ch0["hist_nobs"].get().values()

    cov_post = (
        m["hist_postfit_inclusive_cov"].get().values()
        if "hist_postfit_inclusive_cov" in m
        else None
    )
    cov_pre = (
        m["hist_prefit_inclusive_cov"].get().values()
        if "hist_prefit_inclusive_cov" in m
        else None
    )

    # Fallback: build cov_post from postfit impacts (J J^T, no off-diag).
    # Each impact column is sigma_x_i * dexpdx_i, so J @ J.T ≈ cov_post if
    # postfit nuisance correlations are small. README/T3 note this
    # approximation underestimates true chi² by ~2x but preserves rankings.
    cov_post_source = "saved" if cov_post is not None else None
    if cov_post is None and "hist_postfit_inclusive_global_impacts" in ch0:
        Jpost = ch0["hist_postfit_inclusive_global_impacts"].get().values()
        cov_post = Jpost @ Jpost.T
        cov_post_source = "rebuilt from postfit J@J.T (no off-diag)"
    cov_pre_source = "saved" if cov_pre is not None else None
    if cov_pre is None and "hist_prefit_inclusive_global_impacts" in ch0:
        Jpre = ch0["hist_prefit_inclusive_global_impacts"].get().values()
        cov_pre = Jpre @ Jpre.T
        cov_pre_source = "rebuilt from prefit J@J.T (no off-diag)"

    centers, edges = hist_axis(ch0)

    info = {
        "data": data,
        "pred_post": pred_post,
        "pred_pre": pred_pre,
        "nobs": nobs,
        "cov_post": cov_post,
        "cov_pre": cov_pre,
        "centers": centers,
        "edges": edges,
        "chi2_post": float(m["chi2"]),
        "chi2_pre": float(m.get("chi2_prefit", 0.0) or 0.0),
        "chi2_sat": float(m.get("chi2_saturated", 0.0) or 0.0),
        "ndf": int(m["ndf"]),
        "cov_post_source": cov_post_source,
        "cov_pre_source": cov_pre_source,
    }
    return info


def make_anatomy(info, proj, out_dir):
    data = info["data"]
    pred_pre = info["pred_pre"]
    pred_post = info["pred_post"]
    nobs = info["nobs"]
    centers = info["centers"]
    edges = info["edges"]

    # residual cov = displayed-band cov: cov_post + diag(nobs)
    if info["cov_post"] is None:
        raise RuntimeError(
            "no hist_postfit_inclusive_cov AND no postfit impacts; "
            "re-run with --computeHistCov or --globalImpacts"
        )
    C = info["cov_post"] + np.diag(nobs)
    print(f"  cov_post: {info['cov_post_source']}")
    sigma = np.sqrt(np.diag(C))

    r_pre = pred_pre - data
    r_post = pred_post - data
    dpred = pred_post - pred_pre  # what nuisances added to model

    # per-bin chi2 contribution (diagonal approximation)
    chi2_per_bin_diag = (r_post / sigma) ** 2
    chi2_diag = float(chi2_per_bin_diag.sum())

    # full chi2 reconstruction with off-diagonal
    Cinv_r = np.linalg.solve(C, r_post)
    chi2_full = float(r_post @ Cinv_r)

    # --- 4-panel anatomy figure ---
    fig, axes = plt.subplots(
        4,
        1,
        figsize=(10, 11),
        sharex=True,
        gridspec_kw={"height_ratios": [2.4, 1.2, 1.2, 1.2]},
    )

    # Panel 1: stack
    ax = axes[0]
    ax.errorbar(
        centers, data, yerr=np.sqrt(nobs), fmt="o", ms=3, color="k", label="data"
    )
    ax.step(
        edges,
        np.r_[pred_pre[0], pred_pre],
        where="pre",
        color="C3",
        ls="--",
        label="prefit",
        alpha=0.7,
    )
    ax.step(
        edges, np.r_[pred_post[0], pred_post], where="pre", color="C0", label="postfit"
    )
    band = np.sqrt(np.diag(info["cov_post"]))
    ax.fill_between(
        centers,
        pred_post - band,
        pred_post + band,
        step="mid",
        color="C0",
        alpha=0.2,
        label=r"postfit $\pm 1\sigma$",
    )
    if pred_post.max() > 1e3:
        ax.set_yscale("log")
    ax.set_ylabel("Events / bin")
    title = (
        f"{proj}  chi2/ndf={info['chi2_post']:.1f}/{info['ndf']}  "
        f"(approx-diag={chi2_diag:.1f}, approx-full={chi2_full:.1f}, "
        f"prefit={info['chi2_pre']:.1f})"
    )
    ax.set_title(title)
    ax.legend(loc="best", fontsize=9)

    # Panel 2: prefit vs postfit residual / sigma
    width = np.diff(edges)
    ax = axes[1]
    ax.bar(
        centers,
        r_pre / sigma,
        width=width * 0.9,
        color="C3",
        alpha=0.55,
        label="prefit residual / sigma",
    )
    ax.bar(
        centers,
        r_post / sigma,
        width=width * 0.55,
        color="C0",
        alpha=0.85,
        label="postfit residual / sigma",
    )
    ax.axhline(0, color="k", lw=0.5)
    for thr in (-2, -1, 1, 2):
        ax.axhline(thr, color="grey", lw=0.4, ls=":")
    ax.set_ylabel("(pred - data) / sigma")
    ax.set_ylim(-3.5, 3.5)
    ax.legend(loc="best", fontsize=8, ncol=2)

    # Panel 3: nuisance correction in sigma units
    ax = axes[2]
    ax.bar(
        centers,
        dpred / sigma,
        width=width * 0.85,
        color="C2",
        alpha=0.85,
        label="(pred_post - pred_pre) / sigma  — absorbed by nuisances",
    )
    ax.axhline(0, color="k", lw=0.5)
    for thr in (-2, -1, 1, 2):
        ax.axhline(thr, color="grey", lw=0.4, ls=":")
    ax.set_ylabel("Δpred / sigma")
    ax.set_ylim(-3.5, 3.5)
    ax.legend(loc="best", fontsize=8)

    # Panel 4: per-bin chi² contribution
    ax = axes[3]
    ax.bar(
        centers,
        chi2_per_bin_diag,
        width=width * 0.9,
        color="C7",
        alpha=0.85,
        label=r"per-bin $r_\mathrm{post}^2/\sigma^2$ (diag approx)",
    )
    ax.axhline(1, color="grey", lw=0.4, ls=":")
    ax.set_ylabel(r"$\chi^2$ contribution")
    ax.set_xlabel(proj)
    ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    safe = proj.replace(" ", "_")
    out_pdf = os.path.join(out_dir, f"anatomy_{safe}.pdf")
    out_png = os.path.join(out_dir, f"anatomy_{safe}.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"Saved: {out_pdf}")

    return {
        "C": C,
        "r_post": r_post,
        "r_pre": r_pre,
        "dpred": dpred,
        "sigma": sigma,
        "chi2_diag": chi2_diag,
        "chi2_full": chi2_full,
    }


def make_eigenmodes(anat, info, proj, out_dir, n_show=6, n_top=20):
    C = anat["C"]
    r = anat["r_post"]
    centers = info["centers"]
    edges = info["edges"]

    # Eigendecomposition of C (symmetric PSD). u_k = column of U.
    eigvals, U = np.linalg.eigh(C)
    # sort by descending eigenvalue (so soft → stiff)
    order_eig = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order_eig]
    U = U[:, order_eig]

    # per-mode chi2 contribution: (u_k . r)^2 / lambda_k
    proj_r = U.T @ r
    chi2_modes = proj_r**2 / np.maximum(eigvals, 1e-20)
    chi2_total = float(chi2_modes.sum())

    # rank by descending chi2 contribution
    order_chi2 = np.argsort(chi2_modes)[::-1]

    # --- eigenmode figure ---
    fig, axes = plt.subplots(
        2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [2.0, 1.0]}
    )

    ax = axes[0]
    width = np.diff(edges)
    cumchi2 = 0.0
    cmap = plt.cm.viridis(np.linspace(0.1, 0.9, n_show))
    for i in range(n_show):
        k = order_chi2[i]
        u = U[:, k]
        # orient sign so that u . r > 0 (consistent visual)
        if proj_r[k] < 0:
            u = -u
        ax.plot(
            centers,
            u,
            "-",
            color=cmap[i],
            lw=2,
            label=f"mode #{i+1}: chi²={chi2_modes[k]:.2f} "
            f"(λ={eigvals[k]:.2g}, |u·r|={abs(proj_r[k]):.2g})",
        )
        cumchi2 += chi2_modes[k]
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("eigenvector amplitude")
    ax.set_title(
        f"{proj} — top {n_show} residual chi² modes  "
        f"(cum {cumchi2:.1f} of {chi2_total:.1f}, "
        f"= {cumchi2/chi2_total:.0%} of approx chi²)"
    )
    ax.legend(loc="best", fontsize=8)

    ax = axes[1]
    chi2_top = chi2_modes[order_chi2[:n_top]]
    ax.bar(np.arange(len(chi2_top)), chi2_top, color="C0")
    ax.bar(
        np.arange(len(chi2_top)),
        np.cumsum(chi2_top),
        color="C0",
        alpha=0.15,
        label="cumulative",
    )
    ax.axhline(
        chi2_total,
        color="grey",
        ls="--",
        lw=0.7,
        label=f"total approx chi² = {chi2_total:.1f}",
    )
    ax.set_xlabel("mode rank (sorted by chi² contribution)")
    ax.set_ylabel(r"chi² contribution")
    ax.legend(loc="best", fontsize=8)

    fig.tight_layout()
    safe = proj.replace(" ", "_")
    out_pdf = os.path.join(out_dir, f"eigenmodes_{safe}.pdf")
    out_png = os.path.join(out_dir, f"eigenmodes_{safe}.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    print(f"Saved: {out_pdf}")

    # --- text table ---
    out_txt = os.path.join(out_dir, f"eigen_table_{safe}.txt")
    with open(out_txt, "w") as f:
        f.write(f"# Residual eigenmode decomposition for {proj}\n")
        f.write(
            f"# Approx chi2 = {chi2_total:.3f}, true rabbit chi2 = "
            f"{info['chi2_post']:.3f}\n"
        )
        f.write(f"# C = cov_post + diag(nobs); under-counts true chi2 by ~2x.\n")
        f.write(f"#\n")
        f.write(f"# rank  mode_k  lambda_k        u_k.r        chi2_k    cum_chi2\n")
        cum = 0.0
        for i in range(min(n_top, len(order_chi2))):
            k = order_chi2[i]
            cum += chi2_modes[k]
            f.write(
                f"  {i:4d}  {k:5d}  {eigvals[k]:12.6e}  "
                f"{proj_r[k]:+12.4f}  {chi2_modes[k]:9.3f}  {cum:9.3f}\n"
            )
    print(f"Saved: {out_txt}")

    return chi2_total, order_chi2, eigvals, U, proj_r


def main():
    fitres = sys.argv[1]
    out_dir = sys.argv[2]
    proj = sys.argv[3] if len(sys.argv) > 3 else "Project ch0 ptll"
    os.makedirs(out_dir, exist_ok=True)

    fr, _ = get_fitresult(fitres, meta=True)
    if proj not in fr["mappings"]:
        avail = list(fr["mappings"].keys())
        raise SystemExit(f"projection '{proj}' not in fitresults; available: {avail}")
    info = load_proj(fr, proj)
    print(
        f"Loaded {proj}: {len(info['data'])} bins, "
        f"chi2={info['chi2_post']:.2f}/{info['ndf']}"
    )
    anat = make_anatomy(info, proj, out_dir)
    print(
        f"  approx-diag chi² = {anat['chi2_diag']:.2f}, "
        f"approx-full chi² (with off-diag) = {anat['chi2_full']:.2f}, "
        f"true chi² = {info['chi2_post']:.2f}"
    )
    chi2_total, order_chi2, eigvals, U, proj_r = make_eigenmodes(
        anat, info, proj, out_dir
    )

    # one-line summary
    cum = np.cumsum(np.sort(proj_r**2 / np.maximum(eigvals, 1e-20))[::-1])
    print(f"\n=== {proj} eigenmode summary ===")
    for n in (1, 3, 5, 10, 20):
        if n <= len(cum):
            print(
                f"  top {n:2d} modes: {cum[n-1]:.2f} of {chi2_total:.2f} "
                f"({cum[n-1]/chi2_total:.1%})"
            )


if __name__ == "__main__":
    main()
