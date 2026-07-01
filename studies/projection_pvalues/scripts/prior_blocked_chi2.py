"""Diagnostic: estimate chi² currently 'blocked' by Gaussian priors on
each constrained nuisance, group-summed.

For a nuisance with reported pull = theta_hat and constraint sigma_post
(both in units of prior sigma=1), a parabolic profile likelihood gives
the chi² gain from widening that nuisance's prior to infinity:

    Δchi²_i  =  pull_i² / (1 − sigma_post,i²)

(Derivation: at constraint weight cw and data Hessian α, posterior
gives sigma_post² = 1/(α+cw) and pull = α·theta_data/(α+cw); -2lnL at
the minimum is cw·pull²/(1 − cw·sigma_post²); for cw=1 and cw'=0 the
difference is pull²/(1 − sigma_post²). Diverges as sigma_post → 1
because that limit means data weakly informs the parameter; freeing
the prior could let it absorb an arbitrarily large chi².)

This is the per-nuisance, single-parameter linear prediction. Group sums
add the predictions independently; correlations within a group can
shift the actual gain (typically up, when the group has a coherent
direction the data wants).

Use this as a *forward* diagnostic for "would loosening these priors
help" — complementary to the residual-on-nuisance-basis projection
which only sees what's left over at the current prior widths.

Usage:
    FITRES=... python3 prior_blocked_chi2.py
"""

import os
import re
import sys
import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
from rabbit import io_tools  # noqa: E402

NOI = {"pdfAlphaS"}

# Group definitions: name -> list of regex patterns matched on parm name.
GROUPS = [
    (
        "scetlibNP_lambda",
        [r"^chargeVgenNP0scetlibNPZdelta_lambda", r"^chargeVgenNP0scetlibNPZlambda"],
    ),
    ("scetlibNP_gamma", [r"^scetlibNPgamma"]),
    ("resumScale", [r"^resumFOScaleZ", r"^resumTransitionZ"]),
    ("resumTNP", [r"^resumTNP"]),
    ("QCDscaleZfine_h0", [r"^QCDscaleZfine_PtV.*helicity_0"]),
    ("QCDscaleZfine_h2", [r"^QCDscaleZfine_PtV.*helicity_2"]),
    ("QCDscaleZfine_h5_h7", [r"^QCDscaleZfine_PtV.*helicity_[57]"]),
    ("QCDscaleZfine_other", [r"^QCDscaleZfine_PtV.*helicity_[1346]"]),
    ("QCDscaleZinclusive", [r"^QCDscaleZinclusive"]),
    ("horace_FSR", [r"^horace"]),
    ("mb_pair", [r"^mb_up$", r"^pdfMSHT20mbrange"]),
    ("mc_pair", [r"^mc_", r"^pdfMSHT20mcrange"]),
    ("PDF_other", [r"^pdf(?!AlphaS)(?!MSHT20mbrange)(?!MSHT20mcrange)"]),
    ("effSyst_reco_track", [r"^effSyst_reco", r"^effSyst_tracking"]),
    ("effSyst_iso_trig", [r"^effSyst_iso", r"^effSyst_trigger", r"^effSyst_idip"]),
    ("effStat", [r"^effStat"]),
    ("BBB", [r"^binByBinStat"]),
    ("scaleCorr", [r"^Scale_correction"]),
    ("resolution", [r"^Resolution_correction"]),
    ("pixelMult", [r"^pixel_multiplicity"]),
    ("prefire", [r"^CMS_prefire"]),
    ("photon_induced", [r"^CMS_PhotonInduced"]),
    ("pythia_shower", [r"^pythia_shower"]),
    ("lumi", [r"^lumi"]),
]

# Aggregate "super-groups"
SUPER = [
    ("NP_total (lambda+gamma)", ["scetlibNP_lambda", "scetlibNP_gamma"]),
    ("NP+resum", ["scetlibNP_lambda", "scetlibNP_gamma", "resumScale", "resumTNP"]),
    (
        "ALL theory",
        [
            "scetlibNP_lambda",
            "scetlibNP_gamma",
            "resumScale",
            "resumTNP",
            "QCDscaleZfine_h0",
            "QCDscaleZfine_h2",
            "QCDscaleZfine_h5_h7",
            "QCDscaleZfine_other",
            "QCDscaleZinclusive",
            "horace_FSR",
            "mb_pair",
            "mc_pair",
            "PDF_other",
        ],
    ),
    (
        "ALL detector",
        [
            "effSyst_reco_track",
            "effSyst_iso_trig",
            "effStat",
            "BBB",
            "scaleCorr",
            "resolution",
            "pixelMult",
            "prefire",
            "photon_induced",
            "lumi",
        ],
    ),
]


def assign_group(name, group_defs):
    for gname, patterns in group_defs:
        if any(re.match(p, name) for p in patterns):
            return gname
    return "other"


def main():
    path = os.environ.get("FITRES")
    if path is None:
        if len(sys.argv) > 1:
            path = sys.argv[1]
        else:
            raise SystemExit("usage: FITRES=... or python prior_blocked_chi2.py <path>")

    fr = io_tools.get_fitresult(path)
    labels, pulls, sigmas = io_tools.get_pulls_and_constraints(fr)
    labels = np.asarray(labels)
    pulls = np.asarray(pulls)
    sigmas = np.asarray(sigmas)

    # Filter NOI and obviously-unconstrained nuisances (sigma >= ~1: prior dominates,
    # so widening the prior frees them but they have no data direction either way).
    keep = np.array([n not in NOI for n in labels])
    labels = labels[keep]
    pulls = pulls[keep]
    sigmas = sigmas[keep]

    # tension significance (parabolic): |pull|/sigma_post
    with np.errstate(divide="ignore", invalid="ignore"):
        tension = np.where(sigmas > 0, np.abs(pulls) / sigmas, 0.0)
    # chi² absorbable by widening prior to infinity (single-nuisance linear)
    # Δchi² = pull² / (1 - sigma_post²)   for sigma_prior=1 (constraintweight=1)
    # Sigmas >= ~1 mean prior dominates; clamp denominator to avoid divergence
    # but the divergence is real — those are the most-blocked cases.
    one_minus = 1.0 - sigmas**2
    eps = 1e-4  # clamp denominator: σ_post=0.99995 gives 1-σ²≈1e-4
    blocked_raw = pulls**2 / np.maximum(one_minus, eps)
    # Cap at sigma_cap (default 0.95): single-nuisance Gaussian
    # approximation breaks down for highly correlated nuisance groups
    # (e.g. effStat with 2784 small-pull nuisances each at sigma~0.999).
    # Above sigma_cap the per-nuisance formula inflates spuriously.
    sigma_cap = float(os.environ.get("SIGMA_CAP", "0.95"))
    blocked = np.where(sigmas < sigma_cap, blocked_raw, 0.0)
    # Also retain raw for reporting transparency
    blocked_above_cap = np.where(sigmas >= sigma_cap, blocked_raw, 0.0)
    print(
        f"# σ_cap = {sigma_cap}; "
        f"{int(np.sum(sigmas < sigma_cap))} nuisances kept, "
        f"{int(np.sum(sigmas >= sigma_cap))} dropped above cap"
    )

    print(f"Path: {path}")
    print(f"N constrained-or-NOI: {len(labels)}")
    print(f"Total Σ pull² = {np.sum(pulls**2):.2f}")
    print(f"Total Σ blocked-chi² = {np.sum(blocked):.2f}")
    print(f"  (= chi² potentially absorbed if ALL priors were widened to ∞)")
    print()

    # group assignment
    group_of = np.array([assign_group(n, GROUPS) for n in labels])

    # per-group totals
    rows = []
    for gname, _ in GROUPS:
        idx = np.where(group_of == gname)[0]
        if len(idx) == 0:
            continue
        n = len(idx)
        n_constrained = int(np.sum(sigmas[idx] < 0.99))
        sumpull2 = float(np.sum(pulls[idx] ** 2))
        sumblocked = float(np.sum(blocked[idx]))
        max_blocked = float(np.max(blocked[idx])) if n else 0
        max_blocked_name = labels[idx][np.argmax(blocked[idx])] if n else ""
        rows.append(
            (
                gname,
                n,
                n_constrained,
                sumpull2,
                sumblocked,
                max_blocked,
                max_blocked_name,
            )
        )
    # sort by Σ blocked
    rows.sort(key=lambda r: -r[4])

    print(
        f"{'group':25s} {'n':>4} {'n_con':>5} {'Σpull²':>8} "
        f"{'Σblocked':>9}  {'top-nuis':<45} {'block':>6}"
    )
    print("-" * 110)
    for gname, n, ncon, sp, sb, mb, mn in rows:
        print(
            f"{gname:25s} {n:>4d} {ncon:>5d} {sp:>8.2f} "
            f"{sb:>9.2f}  {mn[:45]:<45} {mb:>6.2f}"
        )

    print()
    print("Aggregate super-groups (Σ over component groups):")
    super_rows = []
    for label, members in SUPER:
        sb = float(np.sum([blocked[group_of == g].sum() for g in members]))
        sp = float(np.sum([(pulls[group_of == g] ** 2).sum() for g in members]))
        super_rows.append((label, sb, sp))
    super_rows.sort(key=lambda r: -r[1])
    for label, sb, sp in super_rows:
        print(f"  {label:35s}  Σblocked = {sb:7.2f}   Σpull² = {sp:7.2f}")

    # top individual nuisances by blocked
    print()
    print("Top 25 individual nuisances by blocked chi² (= candidates to free):")
    order = np.argsort(-blocked)
    print(
        f"{'rank':>4} {'name':45s} {'pull':>7} {'σ_post':>7} "
        f"{'tens':>6} {'block':>7}"
    )
    for k in range(min(25, len(order))):
        i = order[k]
        print(
            f"{k+1:>4d} {labels[i][:45]:45s} {pulls[i]:+7.2f} "
            f"{sigmas[i]:>7.3f} {tension[i]:>6.2f} {blocked[i]:>7.2f}"
        )


if __name__ == "__main__":
    main()
