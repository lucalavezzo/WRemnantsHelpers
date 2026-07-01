"""Decompose the ptll postfit chi2 into diagonal-only vs full (off-diagonal-aware)
contributions, to answer: how much of the small p-value is driven by off-diagonal
terms of cov^-1 vs the per-bin diagonal residuals?

Three covariance candidates:
  C_post  = cov_post + diag(nobs)           # what the "per-bin pull" display uses
  C_systs = J J^T   + diag(nobs)            # rabbit's res_cov approx (prefit widths, no BBB)
  C_diag  = diag(C_post) only               # equivalent to summing per-bin pull^2

For each C: chi2 = r^T C^-1 r. We also report the eigendecomposition of C and
the chi2 contribution per eigenmode (sorted), so you can read off where the
chi2 lives.

Usage:
    python diag_vs_offdiag_chi2.py <fitresults.hdf5> [proj_key]
"""

import os
import sys

import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult  # noqa: E402

NOI_NAMES = {"pdfAlphaS"}


def main():
    fitres = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) > 2 else "Project ch0 ptll"
    fr, _ = get_fitresult(fitres, meta=True)
    m = fr["mappings"][proj]
    ch0 = m["channels"]["ch0"]
    data = ch0["hist_data_obs"].get().values()
    pred_post = ch0["hist_postfit_inclusive"].get().values()
    nobs = ch0["hist_nobs"].get().values()
    cov_post = m["hist_postfit_inclusive_cov"].get().values()
    Jhist = ch0["hist_prefit_inclusive_global_impacts"].get()
    impact_names = list(Jhist.axes[1])
    J_all = Jhist.values()
    keep = np.array([n not in NOI_NAMES for n in impact_names])
    J = J_all[:, keep]

    r = pred_post - data
    chi2_true = float(m["chi2"])
    ndf_true = int(m["ndf"])

    # Three candidate covariance constructions.
    cand = {
        "cov_post + diag(nobs)         (per-bin-pull denominator)": cov_post
        + np.diag(nobs),
        "J J^T   + diag(nobs)          (res_cov approximation)  ": J @ J.T
        + np.diag(nobs),
        "diag(cov_post + nobs) ONLY    (no off-diagonal at all) ": np.diag(
            np.diag(cov_post) + nobs
        ),
    }

    print(f"=== {proj} ===")
    print(f"true chi2 (rabbit)              = {chi2_true:.2f}  /  ndf {ndf_true}")
    print()
    print(f"{'reconstruction':62s} {'chi2':>8s} {'chi2/true':>10s}")
    for label, C in cand.items():
        c = float(r @ np.linalg.solve(C, r))
        print(f"  {label:60s} {c:8.2f}    {c/chi2_true*100:6.1f}%")

    # Same comparison but for ALL projections (printed compactly).
    print()
    print("Diagonal-vs-full breakdown for the chosen reconstruction (cov_post + nobs):")
    C_full = cov_post + np.diag(nobs)
    chi2_full = float(r @ np.linalg.solve(C_full, r))
    chi2_diag = float(np.sum(r**2 / (np.diag(cov_post) + nobs)))
    chi2_offdiag = chi2_full - chi2_diag
    print(
        f"  diag-only chi2  (sum of per-bin pull^2 in the displayed plot) = {chi2_diag:.2f}"
    )
    print(
        f"  full     chi2  (using off-diagonal too)                       = {chi2_full:.2f}"
    )
    print(
        f"  off-diagonal contribution                                     = {chi2_offdiag:+.2f}"
    )
    print(
        f"  off-diag / full                                              = {chi2_offdiag/chi2_full*100:+.1f}%"
    )
    print()

    # Eigendecomposition of C_full and chi2 per eigenmode.
    eigvals, U = np.linalg.eigh(C_full)
    r_proj = U.T @ r  # coords of r in eigenbasis
    chi2_per_mode = (r_proj**2) / eigvals
    order = np.argsort(-chi2_per_mode)
    print("Eigenmode chi2 contribution (top 10 modes of C_full = cov_post+nobs):")
    print(
        f"{'rank':>4} {'eigvalue':>12} {'r·e_k':>10} {'chi2_k':>8} {'cum chi2':>10}  "
        f"{'top |bins|':<25}"
    )
    cum = 0.0
    for k_rank, idx in enumerate(order[:10]):
        cum += chi2_per_mode[idx]
        # Top contributors of this eigenmode (largest |U[i, idx]|).
        v = U[:, idx]
        top = np.argsort(-np.abs(v))[:5]
        top_str = ",".join(str(int(t)) for t in top)
        print(
            f"{k_rank:4d} {eigvals[idx]:12.3e} {r_proj[idx]:+10.2f} {chi2_per_mode[idx]:8.2f} "
            f"{cum:10.2f}  {top_str:<25}"
        )

    print()
    print(
        f"Total chi2 from top-3 modes                                  = "
        f"{sum(chi2_per_mode[order[:3]]):.2f}  ({sum(chi2_per_mode[order[:3]])/chi2_full*100:.0f}% of full)"
    )
    print(
        f"Total chi2 from top-5 modes                                  = "
        f"{sum(chi2_per_mode[order[:5]]):.2f}  ({sum(chi2_per_mode[order[:5]])/chi2_full*100:.0f}% of full)"
    )

    # Also show: bin pulls (diagonal) for context.
    print()
    print("Per-bin diagonal pull r_i / sqrt(C_post_ii + nobs_i):")
    sigma_diag = np.sqrt(np.diag(cov_post) + nobs)
    pulls = r / sigma_diag
    bin_idx_sorted = np.argsort(-np.abs(pulls))
    print(f"{'rank':>4} {'bin':>4} {'r_i':>10} {'sigma_i':>10} {'pull_i':>8}")
    for k_rank, i in enumerate(bin_idx_sorted[:10]):
        print(
            f"{k_rank:4d} {int(i):4d} {r[i]:+10.0f} {sigma_diag[i]:10.0f} {pulls[i]:+8.2f}"
        )


if __name__ == "__main__":
    main()
