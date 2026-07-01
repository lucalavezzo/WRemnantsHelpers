"""T3: reconstruct the residual covariance used in the projection chi2 from
saved hists, eigendecompose it, and rank modes by whitened residual.

Approach (avoids re-running rabbit_fit):
- res_cov used in chi2 (fitter.py:1787-1842) is
    res_cov = J @ var_theta0 * J^T + data_stat + BBB
  where J = d(pred)/d(theta) at the postfit point.
- For unit Gaussian priors var_theta0 = 1, so a +/-1 sigma_prefit = +/-1 step
  in theta gives an impact equal to J_b. The saved hist
  `hist_prefit_inclusive_global_impacts` therefore *is* J columns up to sign
  conventions. NOIs (var_theta0 = 0, e.g. pdfAlphaS) must be excluded.
- data_stat term: with varnobs=None, fitter.py:1814 uses
    res_cov_stat = J_stat @ diag(nobs) @ J_stat^T
  where J_stat = d(pred)/d(nobs). For a Project mapping that just sums
  bins of the same channel, J_stat is the (rectangular) projection matrix,
  so for the projected residual the data-stat contribution reduces to
  diag(nobs_proj). (Verified empirically below by chi2 reproduction.)
- BBB term: not reconstructible from the saved 1D hists alone — it lives in
  the full 4D space and gets projected. We approximate it by adding the
  difference between the saved post-fit prediction cov and the systs-only
  estimate diag of cov_post if needed; in practice the systs+stat already
  reproduce the chi2 well enough for an eigendecomposition.

Usage:
    python dump_rescov.py <fitresults.hdf5> <out_dir> [proj_key]
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult  # noqa: E402

NOI_NAMES = {"pdfAlphaS"}


def reconstruct_rescov(fr, proj_key):
    m = fr["mappings"][proj_key]
    ch0 = m["channels"]["ch0"]
    data = ch0["hist_data_obs"].get().values()
    nobs = ch0["hist_nobs"].get().values()
    pred_post = ch0["hist_postfit_inclusive"].get().values()
    cov_post = m["hist_postfit_inclusive_cov"].get().values()
    J = ch0["hist_prefit_inclusive_global_impacts"].get()
    impacts_axis = J.axes[1]
    impact_names = list(impacts_axis)
    Jvals = J.values()  # (nbins, nimpacts)

    # Drop NOIs (var_theta0=0).
    keep = np.array([n not in NOI_NAMES for n in impact_names])
    J_keep = Jvals[:, keep]

    res = pred_post - data

    # Build res_cov = J J^T + diag(nobs); BBB approximated by max(0, cov_post - J J^T).
    JJt = J_keep @ J_keep.T
    res_cov_systs_stat = JJt + np.diag(nobs)

    # BBB approximation: residual variance in cov_post not explained by
    # systematics (cov_post is dexpdx @ cov @ dexpdx^T + BBB ).
    # Here we add an isotropic floor only on the diagonal so we don't
    # invert a positive correction.
    delta_diag = np.maximum(np.diag(cov_post) - np.diag(JJt), 0.0)
    res_cov = res_cov_systs_stat + np.diag(delta_diag)

    return {
        "res": res,
        "res_cov_systs_stat": res_cov_systs_stat,
        "res_cov_with_bbb_diag": res_cov,
        "cov_post": cov_post,
        "JJt": JJt,
        "data": data,
        "nobs": nobs,
        "pred_post": pred_post,
        "impact_names": [n for n, k in zip(impact_names, keep) if k],
        "J_keep": J_keep,
        "chi2_true": float(m["chi2"]),
        "ndf_true": int(m["ndf"]),
    }


def whitened_eigendecomp(res, res_cov):
    # Use eigendecomposition of res_cov; whitened residual is diag(1/sqrt(eig)) @ U^T @ r
    # where res_cov = U diag(eig) U^T.
    eigvals, U = np.linalg.eigh(res_cov)
    # Numerical floor.
    pos = eigvals > 0
    r_whit = np.zeros(len(eigvals))
    r_proj = U.T @ res  # (n,)
    r_whit[pos] = r_proj[pos] / np.sqrt(eigvals[pos])
    chi2_per_mode = r_whit**2
    return eigvals, U, r_proj, r_whit, chi2_per_mode


def main():
    fitres = sys.argv[1]
    out_dir = sys.argv[2]
    proj = sys.argv[3] if len(sys.argv) > 3 else "Project ch0 ptll"
    os.makedirs(out_dir, exist_ok=True)
    fr, _ = get_fitresult(fitres, meta=True)
    info = reconstruct_rescov(fr, proj)
    res = info["res"]
    chi2_true = info["chi2_true"]

    chi2_a = float(res @ np.linalg.solve(info["res_cov_systs_stat"], res))
    chi2_b = float(res @ np.linalg.solve(info["res_cov_with_bbb_diag"], res))
    chi2_post_only = float(
        res @ np.linalg.solve(info["cov_post"] + np.diag(info["nobs"]), res)
    )
    print(f"--- {proj} ---")
    print(f"chi2_true                   = {chi2_true:.2f}")
    print(f"chi2 systs+stat (JJt+nobs)  = {chi2_a:.2f}")
    print(f"chi2 systs+stat+bbb_diag    = {chi2_b:.2f}")
    print(f"chi2 cov_post + nobs        = {chi2_post_only:.2f}")

    # Pick the cov whose chi2 is closest to true for the eigendecomposition.
    candidates = {
        "systs+stat": (chi2_a, info["res_cov_systs_stat"]),
        "systs+stat+bbb_diag": (chi2_b, info["res_cov_with_bbb_diag"]),
        "cov_post+nobs": (chi2_post_only, info["cov_post"] + np.diag(info["nobs"])),
    }
    best_label = min(candidates.keys(), key=lambda k: abs(candidates[k][0] - chi2_true))
    print(
        f"Using best-matching reconstruction: {best_label} ({candidates[best_label][0]:.2f})"
    )
    cov_used = candidates[best_label][1]

    eigvals, U, r_proj, r_whit, chi2_per_mode = whitened_eigendecomp(res, cov_used)

    order = np.argsort(-chi2_per_mode)
    print("Top modes by chi2 contribution:")
    for k in order[:10]:
        print(
            f"  mode {k:2d}  eigvalue={eigvals[k]:.3e}  r_whit={r_whit[k]:+.2f}  "
            f"chi2_contrib={chi2_per_mode[k]:.2f}"
        )
    cumchi2 = np.cumsum(chi2_per_mode[order])
    print(
        f"chi2 captured by top 1 mode  = {cumchi2[0]:.2f} ({cumchi2[0]/chi2_true*100:.1f}%)"
    )
    print(
        f"chi2 captured by top 3 modes = {cumchi2[2]:.2f} ({cumchi2[2]/chi2_true*100:.1f}%)"
    )
    print(
        f"chi2 captured by top 5 modes = {cumchi2[4]:.2f} ({cumchi2[4]/chi2_true*100:.1f}%)"
    )

    # Plot eigvalue spectrum and chi2 contributions per mode (sorted).
    fig, axs = plt.subplots(1, 3, figsize=(15, 4))
    axs[0].semilogy(np.sort(eigvals)[::-1], "o-")
    axs[0].set_title("eigenvalues of res_cov (descending)")
    axs[0].set_xlabel("mode rank")
    axs[0].set_ylabel("eigenvalue")
    axs[0].grid(True, which="both", ls=":", alpha=0.4)

    axs[1].bar(range(len(chi2_per_mode)), chi2_per_mode[order])
    axs[1].set_title(f"chi2 per mode (sorted), total={chi2_per_mode.sum():.1f}")
    axs[1].set_xlabel("mode rank (largest contribution first)")
    axs[1].set_ylabel("chi2 contribution")
    axs[1].grid(True, ls=":", alpha=0.4)

    # Plot the top 3 contributing modes' shape (eigenvector) over bins.
    centers = np.arange(len(res))
    for k_rank in range(min(3, len(order))):
        k = order[k_rank]
        axs[2].plot(centers, U[:, k], label=f"mode {k} (chi2={chi2_per_mode[k]:.1f})")
    axs[2].axhline(0, color="k", lw=0.5)
    axs[2].set_title(f"top-3 mode shapes ({proj})")
    axs[2].set_xlabel("bin")
    axs[2].set_ylabel("eigenvector amplitude")
    axs[2].legend(fontsize=8)
    axs[2].grid(True, ls=":", alpha=0.4)

    fig.tight_layout()
    safe = proj.replace(" ", "_")
    out = os.path.join(out_dir, f"rescov_eigs_{safe}.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=120)
    plt.close(fig)
    print(f"Saved plot: {out}")

    # Also save numerical dump.
    np.savez(
        os.path.join(out_dir, f"rescov_{safe}.npz"),
        res=res,
        res_cov=cov_used,
        eigvals=eigvals,
        eigvecs=U,
        r_proj=r_proj,
        r_whit=r_whit,
        chi2_per_mode=chi2_per_mode,
        chi2_true=chi2_true,
        method=best_label,
    )


if __name__ == "__main__":
    main()
