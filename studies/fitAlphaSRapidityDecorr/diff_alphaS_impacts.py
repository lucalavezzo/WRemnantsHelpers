#!/usr/bin/env python3
"""
Diagnose what is driving the spread of alphaS values across rapidity bins
in a per-bin-decorrelated alphaS fit.

For each nuisance i with post-fit pull theta_hat_i (in prefit-sigma units)
and impact I_ij = d(alphaS_j)/d(theta_i) * sigma_theta_i (in POI units),
we report:

  mean_i   = mean_j  I_ij                    -> "global-alphaS-equivalent" lever
  spread_i = max_j I_ij - min_j I_ij         -> capacity to spread the bins
  std_i    = std_j   I_ij                    -> rms version of capacity
  delta_i  = spread_i * theta_hat_i          -> currently active spread contribution
  contrib_ijk = (I_ij - I_ik) * theta_hat_i  -> per-pair driver

Sanity checks:
  - For each POI j: sum_i (I_ij * theta_hat_i) should ~ (alphaS_j_postfit - alphaS_j_prefit).
  - For each pair (j, k): sum_i (I_ij - I_ik) * theta_hat_i should ~ (alphaS_j - alphaS_k)_postfit.

Usage:
    diff_alphaS_impacts.py results/fitresults.hdf5 \
        --poiRegex '^alphaS_y\d+$' --topN 20

The fit must have been run with --doImpacts --globalImpacts (default impactType
here is "global").
"""

import argparse
import re
import sys

import numpy as np

from rabbit import io_tools


def make_parser():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("infile", help="Path to fitresults.hdf5 (decorrelated alphaS fit)")
    p.add_argument(
        "--inclusive",
        default=None,
        help="Optional path to fitresults.hdf5 from the *inclusive* "
        "(non-decorrelated) alphaS fit. If given, the script also "
        "prints the likelihood-ratio test "
        "chi2 = 2*(NLL_incl - NLL_decorr) ~ chi2(N_y - 1), the "
        "appropriate compatibility test by Wilks' theorem.",
    )
    p.add_argument(
        "--result",
        default=None,
        help="Result key inside the fitresults file (e.g. 'asimov'). "
        "Default: data result if present, else asimov.",
    )
    p.add_argument(
        "--poiRegex",
        required=True,
        help="Regex selecting the per-bin alphaS POIs, e.g. '^alphaS_y\\d+$'.",
    )
    p.add_argument(
        "--impactType",
        default="global",
        choices=["global", "gaussian_global", "traditional", "nonprofiled"],
        help="Which impact flavor to read (default: global).",
    )
    p.add_argument(
        "--grouped",
        action="store_true",
        help="Use rabbit's grouped impacts instead of per-nuisance.",
    )
    p.add_argument(
        "--topN",
        type=int,
        default=20,
        help="How many top entries to print per ranking.",
    )
    p.add_argument(
        "--pair",
        nargs=2,
        metavar=("POI_A", "POI_B"),
        default=None,
        help="Restrict per-pair contribution analysis to this POI pair. "
        "Default: the pair with the largest postfit alphaS difference.",
    )
    p.add_argument(
        "--groupBy",
        default=None,
        help="Optional regex with named groups to aggregate nuisances. "
        "Each nuisance is assigned to the first matching named group. "
        "Example: --groupBy 'pdf(?P<pdf>.*)|(?P<recoil>recoil.*)|(?P<fsr>fsr.*)'.",
    )
    p.add_argument(
        "--minSpread",
        type=float,
        default=0.0,
        help="Hide nuisances whose impact spread is below this absolute value.",
    )
    p.add_argument(
        "--csv",
        default=None,
        help="Optional path to write the full per-nuisance table as CSV.",
    )
    return p


def load_poi_table(fitresult, poi_names, impact_type, grouped):
    """Read impacts for each POI, align nuisance labels, return matrix.

    Returns
    -------
    nuis_labels : (Nnuis,) array of str
    I           : (Npoi, Nnuis) impact matrix (NaN where a POI is missing a label)
    """
    rows = []
    label_lists = []
    for poi in poi_names:
        impacts, labels = io_tools.read_impacts_poi(
            fitresult,
            poi,
            grouped=grouped,
            impact_type=impact_type,
            add_total=False,
        )
        labels = np.array([str(l) for l in labels])
        rows.append((labels, np.asarray(impacts, dtype=np.float64)))
        label_lists.append(labels)

    # union of labels, preserving first-seen order
    seen = {}
    for labels in label_lists:
        for l in labels:
            if l not in seen:
                seen[l] = len(seen)
    union = np.array(list(seen.keys()))

    I = np.full((len(poi_names), len(union)), np.nan, dtype=np.float64)
    for r, (labels, impacts) in enumerate(rows):
        idx = np.array([seen[l] for l in labels])
        I[r, idx] = impacts
    return union, I


def align_pulls(nuis_labels, pull_labels, pulls):
    """Return pulls reordered/filtered to match `nuis_labels`. Missing -> 0."""
    pull_index = {str(l): i for i, l in enumerate(pull_labels)}
    out = np.zeros(len(nuis_labels), dtype=np.float64)
    missing = []
    for i, l in enumerate(nuis_labels):
        if l in pull_index:
            out[i] = pulls[pull_index[l]]
        else:
            missing.append(l)
    return out, missing


def get_poi_central_and_sigma(fitresult, poi_names, prefit=False):
    name = "parms_prefit" if prefit else "parms"
    h = fitresult[name].get()
    labels = np.array([str(l) for l in h.axes["parms"]])
    values = h.values()
    sigmas = np.sqrt(h.variances())
    idx = {l: i for i, l in enumerate(labels)}
    centrals = np.array([values[idx[p]] for p in poi_names])
    errs = np.array([sigmas[idx[p]] for p in poi_names])
    return centrals, errs


def assign_groups(nuis_labels, group_regex):
    """Return array of group names, one per nuisance.

    group_regex is a single regex with named capture groups; each nuisance is
    tagged with the name of the first matching group. Unmatched -> 'other'.
    """
    pat = re.compile(group_regex)
    groups = []
    for l in nuis_labels:
        m = pat.match(l) or pat.search(l)
        tag = "other"
        if m:
            for name, val in m.groupdict().items():
                if val is not None:
                    tag = name
                    break
        groups.append(tag)
    return np.array(groups)


def aggregate_by_group(group_tags, *arrays):
    """Group-level sums for impact-like quantities.

    Returns dict tag -> tuple of summed arrays (linear, with sign).
    For non-additive metrics (spread, std) the caller should recompute from the
    matrix; this helper is for additive quantities (delta, mean, contrib).
    """
    result = {}
    unique = sorted(set(group_tags))
    for u in unique:
        mask = group_tags == u
        result[u] = tuple(a[mask].sum() for a in arrays)
    return result


def fmt(x, n=5):
    if isinstance(x, str):
        return x
    if not np.isfinite(x):
        return "nan"
    return f"{x:+.{n}g}"


def print_table(title, rows, headers, sort_key=None, reverse=True, top=None):
    print(f"\n=== {title} ===")
    if sort_key is not None:
        rows = sorted(rows, key=sort_key, reverse=reverse)
    if top is not None:
        rows = rows[:top]
    widths = [
        max(len(str(headers[i])), max((len(str(r[i])) for r in rows), default=0))
        for i in range(len(headers))
    ]
    line = "  ".join(str(headers[i]).ljust(widths[i]) for i in range(len(headers)))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[i]).ljust(widths[i]) for i in range(len(headers))))


def main():
    args = make_parser().parse_args()

    fitresult, meta = io_tools.get_fitresult(args.infile, args.result, meta=True)

    all_pois = io_tools.get_poi_names(meta)
    pat = re.compile(args.poiRegex)
    poi_names = np.array([p for p in all_pois if pat.match(p)])
    if len(poi_names) < 2:
        sys.exit(f"Need >=2 POIs matching {args.poiRegex}; found {list(poi_names)}")
    print(f"Selected {len(poi_names)} POIs: {list(poi_names)}")

    nuis_labels, I = load_poi_table(fitresult, poi_names, args.impactType, args.grouped)
    print(
        f"Loaded {len(nuis_labels)} {'grouped' if args.grouped else 'individual'} "
        f"{args.impactType} impact entries per POI."
    )

    pull_labels, pulls, _ = io_tools.get_pulls_and_constraints(fitresult)
    theta_hat, missing = align_pulls(nuis_labels, pull_labels, pulls)
    if missing:
        print(
            f"NOTE: {len(missing)} impact labels have no matching post-fit pull "
            f"(treated as 0). Examples: {missing[:5]}"
        )

    centrals, sigmas = get_poi_central_and_sigma(fitresult, poi_names)
    centrals_pre, _ = get_poi_central_and_sigma(fitresult, poi_names, prefit=True)
    raw_shift = centrals - centrals_pre
    # If --blindingGroup was used, all selected POIs share an identical additive
    # blinding offset that survives in 'parms' but not in 'parms_prefit'. Estimate
    # and remove it so the per-POI shifts are interpretable. The robust estimator
    # is the median across POIs (the per-bin shifts due to the fit itself average
    # ~ 0 for noi-style alphaS POIs); spread metrics are invariant under this.
    blinding_offset = float(np.median(raw_shift))
    shift = raw_shift - blinding_offset
    spread_obs = centrals.max() - centrals.min()
    j_max = int(np.argmax(centrals))
    j_min = int(np.argmin(centrals))

    print("\n=== Per-POI postfit (BLINDED if --blindingGroup was used) ===")
    print(
        f"Estimated common blinding offset (median postfit-prefit) = "
        f"{fmt(blinding_offset)} (subtracted in 'shift' below)."
    )
    print(
        f"{'POI':<35} {'central':>12} {'sigma':>12} "
        f"{'shift/sigma':>12} {'shift':>12}"
    )
    for p, c, s, sh in zip(poi_names, centrals, sigmas, shift):
        z = sh / s if s > 0 else float("nan")
        print(f"{p:<35} {fmt(c):>12} {fmt(s):>12} {fmt(z):>12} {fmt(sh):>12}")
    print(
        f"Observed spread (max-min): {fmt(spread_obs)}  "
        f"between {poi_names[j_max]} and {poi_names[j_min]}"
    )
    if np.median(sigmas) > 0:
        print(f"  ~ {spread_obs / np.median(sigmas):+.2f} x median(sigma_POI)")

    # Likelihood-ratio compatibility test (Wilks). This is the correct overall
    # test for "is one common alphaS sufficient?".
    if args.inclusive is not None:
        from scipy.stats import chi2 as _chi2

        nll_decorr = float(fitresult["nllvalreduced"][...])
        f_incl = io_tools.get_fitresult(args.inclusive, args.result)
        nll_incl = float(f_incl["nllvalreduced"][...])
        ndf = len(poi_names) - 1
        chi2_lr = 2.0 * (nll_incl - nll_decorr)
        p_lr = 1.0 - _chi2.cdf(chi2_lr, ndf)
        print("\n=== Likelihood-ratio compatibility test (Wilks) ===")
        print(f"  NLL_inclusive  = {nll_incl:.4f}")
        print(f"  NLL_decorr     = {nll_decorr:.4f}")
        print(f"  chi2 = 2*(NLL_inc - NLL_dec) = {chi2_lr:.3f}")
        print(f"  ndf  = N_POI - 1             = {ndf}")
        print(f"  p-value                       = {p_lr:.3g}")
        if "nllvalfull" in fitresult.keys():
            try:
                nll_decorr_f = float(fitresult["nllvalfull"][...])
                nll_incl_f = float(f_incl["nllvalfull"][...])
                chi2_lr_f = 2.0 * (nll_incl_f - nll_decorr_f)
                p_lr_f = 1.0 - _chi2.cdf(chi2_lr_f, ndf)
                print(
                    f"  (full likelihood) chi2 = {chi2_lr_f:.3f}, " f"p = {p_lr_f:.3g}"
                )
            except Exception:
                pass

    # Per-nuisance metrics
    mean_I = np.nanmean(I, axis=0)
    max_I = np.nanmax(I, axis=0)
    min_I = np.nanmin(I, axis=0)
    spread_I = max_I - min_I
    std_I = np.nanstd(I, axis=0, ddof=1)
    delta = spread_I * theta_hat  # active extreme-pair contribution
    delta_std = std_I * theta_hat  # active bulk-spread contribution
    abs_delta = np.abs(delta)
    abs_delta_std = np.abs(delta_std)
    mean_contrib = mean_I * theta_hat  # contribution to the *mean* alphaS

    # Linearized differential decomposition.
    # NOTE: Sum_i I_ij * theta_hat_i is NOT an identity for the postfit POI shift
    # in a profile likelihood -- it captures the linearised contribution from
    # nuisance pulls but misses the data-driven constraint on the POI given the
    # nuisances. So treat the numbers below as a *partial* decomposition useful
    # for ranking which nuisances are most differential, not as a "% explained".
    # The correct overall compatibility test is the LR test above.
    pred_postfit_shift = (I * theta_hat[None, :]).sum(axis=1)  # per POI
    pred_pair = (I[j_max] - I[j_min]) * theta_hat
    pred_spread = pred_pair.sum()

    print("\n=== Linearised differential decomposition (PARTIAL, not an identity) ===")
    print(f"{'POI':<35} {'shift':>14} {'sum I*theta':>14}")
    for p, sh, pr in zip(poi_names, shift, pred_postfit_shift):
        print(f"{p:<35} {fmt(sh):>14} {fmt(pr):>14}")
    print(
        f"Observed spread {fmt(spread_obs)},  "
        f"linearised differential pull sum {fmt(pred_spread)}."
    )
    print(
        f"  [These need not match: profiled-POI movement also has a data-driven "
        f"piece beyond Sum I*theta.]"
    )

    # Apply minSpread filter
    keep = spread_I >= args.minSpread

    # Ranking 1: |delta| = active differential contribution
    rows = []
    for i, l in enumerate(nuis_labels):
        if not keep[i]:
            continue
        rows.append(
            (
                l,
                fmt(theta_hat[i]),
                fmt(mean_I[i]),
                fmt(spread_I[i]),
                fmt(std_I[i]),
                fmt(delta[i]),
                f"{abs_delta[i]:.4g}",
            )
        )
    print_table(
        f"Top {args.topN} nuisances by |spread x pull|  (currently driving the spread)",
        rows,
        (
            "nuisance",
            "pull",
            "mean_I",
            "spread_I",
            "std_I",
            "delta=spread*pull",
            "|delta|",
        ),
        sort_key=lambda r: float(r[-1]),
        top=args.topN,
    )

    # Ranking 2: spread alone (capacity)
    rows2 = []
    for i, l in enumerate(nuis_labels):
        if not keep[i]:
            continue
        rows2.append(
            (
                l,
                fmt(theta_hat[i]),
                fmt(mean_I[i]),
                fmt(spread_I[i]),
                fmt(std_I[i]),
                f"{abs(spread_I[i]):.4g}",
            )
        )
    print_table(
        f"Top {args.topN} nuisances by |spread_I|  (capacity, regardless of pull)",
        rows2,
        ("nuisance", "pull", "mean_I", "spread_I", "std_I", "|spread_I|"),
        sort_key=lambda r: float(r[-1]),
        top=args.topN,
    )

    # Ranking 3: std_I x pull -- robust analogue of |spread x pull|.
    # Uses rms across the 20 POIs of the impact column, weighted by the
    # postfit pull. Less outlier-sensitive than spread and the natural
    # heuristic for "which nuisances drive the *bulk* spread" (the rms
    # spread of alphaS values across bins) rather than the extreme pair.
    rows3 = []
    for i, l in enumerate(nuis_labels):
        if not keep[i]:
            continue
        rows3.append(
            (
                l,
                fmt(theta_hat[i]),
                fmt(mean_I[i]),
                fmt(spread_I[i]),
                fmt(std_I[i]),
                fmt(delta_std[i]),
                f"{abs_delta_std[i]:.4g}",
            )
        )
    print_table(
        f"Top {args.topN} nuisances by |std_I x pull|  "
        f"(active bulk-spread driver; rms-based, outlier-robust)",
        rows3,
        (
            "nuisance",
            "pull",
            "mean_I",
            "spread_I",
            "std_I",
            "delta=std*pull",
            "|delta_std|",
        ),
        sort_key=lambda r: float(r[-1]),
        top=args.topN,
    )

    # Ranking 4: std alone (bulk capacity)
    rows4 = []
    for i, l in enumerate(nuis_labels):
        if not keep[i]:
            continue
        rows4.append(
            (
                l,
                fmt(theta_hat[i]),
                fmt(mean_I[i]),
                fmt(spread_I[i]),
                fmt(std_I[i]),
                f"{abs(std_I[i]):.4g}",
            )
        )
    print_table(
        f"Top {args.topN} nuisances by |std_I|  "
        f"(bulk capacity, regardless of pull)",
        rows4,
        ("nuisance", "pull", "mean_I", "spread_I", "std_I", "|std_I|"),
        sort_key=lambda r: float(r[-1]),
        top=args.topN,
    )

    # Per-pair contributions
    if args.pair is not None:
        try:
            ja = list(poi_names).index(args.pair[0])
            jb = list(poi_names).index(args.pair[1])
        except ValueError:
            sys.exit(f"--pair {args.pair} not in selected POIs {list(poi_names)}")
    else:
        ja, jb = j_max, j_min
    pair_label = f"{poi_names[ja]} - {poi_names[jb]}"
    contrib = (I[ja] - I[jb]) * theta_hat
    obs_pair = centrals[ja] - centrals[jb]
    rows3 = []
    for i, l in enumerate(nuis_labels):
        if not keep[i]:
            continue
        rows3.append(
            (
                l,
                fmt(theta_hat[i]),
                fmt(I[ja, i]),
                fmt(I[jb, i]),
                fmt(contrib[i]),
                f"{abs(contrib[i]):.4g}",
            )
        )
    print_table(
        f"Top {args.topN} contributors to ({pair_label})  "
        f"observed={fmt(obs_pair)}, linearized sum={fmt(contrib.sum())}",
        rows3,
        (
            "nuisance",
            "pull",
            f"I[{poi_names[ja]}]",
            f"I[{poi_names[jb]}]",
            "(Ia-Ib)*pull",
            "|contrib|",
        ),
        sort_key=lambda r: float(r[-1]),
        top=args.topN,
    )

    # Optional group aggregation
    if args.groupBy is not None:
        tags = assign_groups(nuis_labels, args.groupBy)
        agg_delta = {}
        agg_mean = {}
        agg_pair = {}
        agg_quad_spread = {}
        for tag in sorted(set(tags)):
            mask = tags == tag
            agg_delta[tag] = float(np.nansum(delta[mask]))
            agg_mean[tag] = float(np.nansum(mean_contrib[mask]))
            agg_pair[tag] = float(np.nansum(contrib[mask]))
            # group-level spread is non-additive; sum in quadrature as a heuristic
            agg_quad_spread[tag] = float(np.sqrt(np.nansum(spread_I[mask] ** 2)))
        rows4 = [
            (
                tag,
                fmt(agg_mean[tag]),
                fmt(agg_delta[tag]),
                fmt(agg_quad_spread[tag]),
                fmt(agg_pair[tag]),
                f"{abs(agg_pair[tag]):.4g}",
            )
            for tag in agg_delta
        ]
        print_table(
            f"Group-level contributions to ({pair_label})",
            rows4,
            (
                "group",
                "sum mean*pull",
                "sum delta",
                "sqrt(sum spread^2)",
                "sum pair contrib",
                "|pair contrib|",
            ),
            sort_key=lambda r: float(r[-1]),
            top=None,
        )

    if args.csv:
        import csv

        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            header = (
                ["nuisance", "pull"]
                + [f"I[{p}]" for p in poi_names]
                + ["mean_I", "spread_I", "std_I", "delta", "pair_contrib"]
            )
            w.writerow(header)
            for i, l in enumerate(nuis_labels):
                w.writerow(
                    [l, theta_hat[i]]
                    + list(I[:, i])
                    + [mean_I[i], spread_I[i], std_I[i], delta[i], contrib[i]]
                )
        print(f"\nWrote per-nuisance table to {args.csv}")


if __name__ == "__main__":
    main()
