"""T10: Project the postfit ptll residual onto each nuisance's prefit
shape direction (`hist_prefit_inclusive_global_impacts`) to identify
whether the residual lies inside or orthogonal to the NP / resum / etc
subspaces.

For each nuisance i with shape J_i = column i of prefit_global_impacts,
the linear chi2 contribution captured by moving theta_i alone is
    Δchi2_i = (r·J_i)^2 / (J_i·J_i + sigma2_data)
where sigma2_data is the diagonal data-stat term. We also report
    delta_theta_implied = -(r·J_i) / (J_i·J_i)
i.e. the prefit-sigma shift in theta_i that would zero the linear
projection (compared to the existing postfit theta_i and its prior).

Group analogues are computed for nuisance groups (NP, resum, QCDscale,
helicity, eff, BBB, ...) by stacking columns and solving the
constrained least-squares J_g a = -r → chi2 absorbed by group g.

Usage:
    python residual_on_nuisance_basis.py <fitresults.hdf5> <out_dir>
        [proj_key="Project ch0 ptll"]
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")

from rabbit.io_tools import get_fitresult  # noqa: E402

NOI_NAMES = {"pdfAlphaS"}

# Group definitions — name → list of regex prefixes (matched on parm name).
GROUPS = {
    "scetlibNP_lambda": [
        "chargeVgenNP0scetlibNPZdelta_lambda",
        "chargeVgenNP0scetlibNPZlambda",
    ],
    "scetlibNP_eigvar": ["scetlibNPgammaEigvar"],
    "resumScale": ["resumFOScaleZ", "resumTransitionZ"],
    "resumTNP": ["resumTNP_b_"],
    "QCDscaleZfine_h0": None,  # filled below by token match
    "QCDscaleZfine_h2": None,
    "QCDscaleZfine_h5_h7": None,
    "QCDscaleZinclusive": ["QCDscaleZinclusive_PtV"],
    "QCDscaleZfine_all": ["QCDscaleZfine_PtV"],
    "horace_FSR": ["horace"],
    "mb_pair": ["mb_up", "pdfMSHT20mbrange"],
    "mc_pair": ["pdfMSHT20mcrange"],
    "PDF_CT18Z": ["pdfCT18Z"],
    "effSyst_reco_track": ["effSyst_reco_", "effSyst_tracking_"],
    "effSyst_iso_trig": ["effSyst_iso_", "effSyst_trigger_", "effSyst_idip_"],
    "effStat_all": ["effStat_"],
    "BBB": ["binByBinStat_"],
    "scaleCorr": ["Scale_correction_"],
    "pixelMult": ["pixel_multiplicity_"],
    "prefire": ["CMS_prefire"],
}


def fill_helicity_groups(impact_names):
    """Populate helicity-specific QCDscaleZfine groups by helicity index."""
    h0 = []
    h2 = []
    h57 = []
    for n in impact_names:
        if n.startswith("QCDscaleZfine_PtV") and "helicity_" in n:
            idx = n.find("helicity_")
            tail = n[idx + len("helicity_") :]
            hnum = tail.split("_")[0]
            try:
                h = int(hnum)
            except ValueError:
                continue
            if h == 0:
                h0.append(n)
            elif h == 2:
                h2.append(n)
            elif h in (5, 7):
                h57.append(n)
    return {
        "QCDscaleZfine_h0": h0,
        "QCDscaleZfine_h2": h2,
        "QCDscaleZfine_h5_h7": h57,
    }


def main():
    fitres = sys.argv[1]
    out_dir = sys.argv[2]
    proj = sys.argv[3] if len(sys.argv) > 3 else "Project ch0 ptll"
    os.makedirs(out_dir, exist_ok=True)
    fr, _ = get_fitresult(fitres, meta=True)
    m = fr["mappings"][proj]
    ch0 = m["channels"]["ch0"]
    data = ch0["hist_data_obs"].get().values()
    pred_post = ch0["hist_postfit_inclusive"].get().values()
    nobs = ch0["hist_nobs"].get().values()
    Jhist = ch0["hist_prefit_inclusive_global_impacts"].get()
    impact_names = list(Jhist.axes[1])
    J = Jhist.values()  # (nbins, nimpacts)
    res = pred_post - data
    chi2_true = float(m["chi2"])

    keep = np.array([n not in NOI_NAMES for n in impact_names])
    impact_names = [n for n, k in zip(impact_names, keep) if k]
    J = J[:, keep]

    # Per-nuisance scalar projection using only systs cov + diag(nobs).
    sigma2_d = nobs
    cov_systs_stat = J @ J.T + np.diag(sigma2_d)

    # Pre-compute Cinv @ r once.
    Cinv_r = np.linalg.solve(cov_systs_stat, res)
    chi2_systs_stat = float(res @ Cinv_r)

    rJ = J.T @ res  # (nimpacts,)
    JJ = np.einsum("bi,bi->i", J, J)  # (nimpacts,)
    # Per-nuisance "1D" chi2 absorption using the prior + Poisson denominator.
    chi2_per_nuis_diag = rJ**2 / np.maximum(JJ + 1e-30, 1e-30)
    delta_theta_implied = -rJ / np.maximum(JJ + 1e-30, 1e-30)

    # Per-nuisance "marginalized" chi2 absorption: using full covariance
    # excluding nuisance i is expensive; approximate via Sherman-Morrison.
    # Δchi2 absorbed by adding nuisance i with prior width 1 and shape J_i:
    #   Δchi2 = (J_i^T C0^{-1} r)^2 / (1 + J_i^T C0^{-1} J_i)
    # where C0 is the data-only cov diag(nobs). Useful for "what the prior
    # has to absorb if it were the only freedom."
    Cdata = np.diag(sigma2_d)
    Cdata_inv = np.diag(1.0 / sigma2_d)
    Cdr = Cdata_inv @ res  # (nbins,)
    Jt_Cinv_r = J.T @ Cdr  # (nimpacts,)
    Jt_Cinv_J = np.einsum("bi,bi->i", J, Cdata_inv @ J)
    chi2_per_nuis_marg_to_data = (Jt_Cinv_r**2) / (1.0 + Jt_Cinv_J)

    # Print per-nuisance top entries.
    order = np.argsort(-chi2_per_nuis_marg_to_data)
    print(f"--- Per-nuisance projection on {proj} ---")
    print(f"chi2_true (postfit, full cov) = {chi2_true:.2f}")
    print(
        f"chi2_recon (J J^T + diag(nobs)) = {chi2_systs_stat:.2f}  "
        f"(absolute reconstruction known to underestimate by ~2x)"
    )
    print()
    print(
        "Top 25 nuisances by single-nuisance chi2 absorbable from data-only baseline:"
    )
    print(
        f"{'rank':>4} {'name':50s} {'r·J':>8} {'sqrt(JJ)':>8} {'Δchi2_data':>10} {'δθ_implied':>10}"
    )
    for k, idx in enumerate(order[:25]):
        print(
            f"{k:4d} {impact_names[idx]:50s} {rJ[idx]:+8.2f} "
            f"{np.sqrt(JJ[idx]):8.2f} {chi2_per_nuis_marg_to_data[idx]:10.2f} "
            f"{delta_theta_implied[idx]:+10.2f}"
        )

    # Group projection: take all nuisances in group, compute residual norm
    # difference when restricting to that subspace.
    helicity_groups = fill_helicity_groups(impact_names)
    rows = []
    n_in_group = {}
    for gname in list(GROUPS.keys()):
        prefixes = GROUPS[gname]
        if prefixes is None:
            members = helicity_groups.get(gname, [])
        else:
            members = [
                n for n in impact_names if any(n.startswith(p) for p in prefixes)
            ]
        idx = np.array([impact_names.index(n) for n in members], dtype=int)
        n_in_group[gname] = len(idx)
        if len(idx) == 0:
            continue
        Jg = J[:, idx]
        # solve (Jg^T Cdata_inv Jg + I) a = Jg^T Cdata_inv r  → "ridge" with prior I.
        A = Jg.T @ Cdata_inv @ Jg + np.eye(len(idx))
        b = Jg.T @ Cdata_inv @ res
        try:
            a = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            continue
        # delta-residual after the group repulls by a (relative to data-only fit baseline).
        r_after = res - Jg @ a
        chi2_before = float(res @ Cdata_inv @ res)
        chi2_after = float(r_after @ Cdata_inv @ r_after) + float(
            a @ a
        )  # +prior penalty
        absorbed = chi2_before - chi2_after
        rms_a = float(np.sqrt(np.mean(a**2)))
        max_a = float(np.max(np.abs(a)))
        rows.append((gname, len(idx), absorbed, chi2_before, chi2_after, rms_a, max_a))

    print()
    print(
        "--- Group-level absorption (from data-only baseline; chi2_data="
        f"{float(res @ Cdata_inv @ res):.1f} ) ---"
    )
    print(
        f"{'group':25s} {'n':>4} {'Δchi2_absorbed':>14} {'rms_θ_implied':>13} "
        f"{'max_|θ|_implied':>15}"
    )
    rows.sort(key=lambda r: -r[2])
    for gname, n, absorbed, c0, c1, rms_a, max_a in rows:
        print(f"{gname:25s} {n:4d} {absorbed:14.1f} {rms_a:13.2f} {max_a:15.2f}")

    # Summary: scetlibNP sum, theory sum, eff sum.
    print()
    print("Aggregate subspaces:")
    for label, gnames in [
        (
            "ALL theory (NP+resum+QCDscaleZfine+QCDscaleZinclusive+horace+mb+mc+PDF)",
            [
                "scetlibNP_lambda",
                "scetlibNP_eigvar",
                "resumScale",
                "resumTNP",
                "QCDscaleZfine_all",
                "QCDscaleZinclusive",
                "horace_FSR",
                "mb_pair",
                "mc_pair",
                "PDF_CT18Z",
            ],
        ),
        (
            "ALL detector (eff+BBB+scaleCorr+pixelMult+prefire)",
            [
                "effSyst_reco_track",
                "effSyst_iso_trig",
                "effStat_all",
                "BBB",
                "scaleCorr",
                "pixelMult",
                "prefire",
            ],
        ),
        ("scetlibNP only (lambda + eigvar)", ["scetlibNP_lambda", "scetlibNP_eigvar"]),
    ]:
        members = []
        for g in gnames:
            prefixes = GROUPS.get(g)
            if prefixes is None:
                members.extend(helicity_groups.get(g, []))
            else:
                if prefixes:
                    members.extend(
                        [
                            n
                            for n in impact_names
                            if any(n.startswith(p) for p in prefixes)
                        ]
                    )
        members = list(dict.fromkeys(members))  # de-dup, preserve order
        if not members:
            continue
        idx = np.array([impact_names.index(n) for n in members], dtype=int)
        Jg = J[:, idx]
        A = Jg.T @ Cdata_inv @ Jg + np.eye(len(idx))
        b = Jg.T @ Cdata_inv @ res
        try:
            a = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            print(f"  {label}: solve failed, n={len(idx)}")
            continue
        r_after = res - Jg @ a
        chi2_before = float(res @ Cdata_inv @ res)
        chi2_after = float(r_after @ Cdata_inv @ r_after)
        prior_pen = float(a @ a)
        absorbed = chi2_before - (chi2_after + prior_pen)
        max_a = float(np.max(np.abs(a)))
        n_above_2sig = int(np.sum(np.abs(a) > 2.0))
        print(
            f"  {label:65s} n={len(idx):4d}  Δchi2={absorbed:7.1f}  "
            f"residual_chi2_after={chi2_after:7.1f}  max|θ|={max_a:5.2f}  "
            f"n(|θ|>2σ)={n_above_2sig}"
        )

    # Bar chart of top-25 nuisances and group bar chart.
    fig, axes = plt.subplots(2, 1, figsize=(11, 9))
    top = order[:25]
    axes[0].barh(
        range(len(top)),
        chi2_per_nuis_marg_to_data[top][::-1],
        tick_label=[impact_names[t] for t in top[::-1]],
    )
    axes[0].set_xlabel("Δchi2 absorbed (single nuisance, prior=1, data-only baseline)")
    axes[0].set_title(f"top-25 nuisances aligned with {proj} residual")

    rows_sorted = sorted(rows, key=lambda r: -r[2])[:18]
    axes[1].barh(
        range(len(rows_sorted)),
        [r[2] for r in rows_sorted][::-1],
        tick_label=[f"{r[0]} (n={r[1]})" for r in rows_sorted][::-1],
    )
    axes[1].set_xlabel(
        "Δchi2 absorbed by group (least-squares with prior, data-only baseline)"
    )
    axes[1].set_title(f"group-level alignment with {proj} residual")
    fig.tight_layout()
    safe = proj.replace(" ", "_")
    out = os.path.join(out_dir, f"residual_basis_alignment_{safe}.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=120)
    plt.close(fig)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
