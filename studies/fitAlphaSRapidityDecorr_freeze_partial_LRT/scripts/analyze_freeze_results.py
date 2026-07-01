#!/usr/bin/env python3
"""
Tabulate per-bin alphaS spread (and NLL) across the freeze-group refits.

Reads:
  - one baseline decorrelated fitresults file (no freeze)
  - one fitresults file per frozen group (output of run_freeze_groups.py)
  - optionally an inclusive-baseline fitresults file (no freeze, single
    common alphaS) for the full Wilks LRT

For each fit it pulls the per-bin alphaS POI values, computes the spread
(max-min), the rms around the mean, the NLL, and the change in NLL relative
to the unfrozen baseline. With --inclusive it also prints the Wilks LR test
chi2 = 2*(NLL_incl - NLL_decorr) ~ chi2(N_y - 1) at the unfrozen baseline
(the tests with frozen-inclusive partner fits are not auto-run yet; see
the README).

Usage:
    python3 analyze_freeze_results.py --baseline <decorr.h5> \
        --frozen group_name=<file.h5> [group_name2=<file2.h5> ...] \
        [--inclusive <inclusive.h5>] \
        [--poiRegex '^.*AlphaS.*yll_decorr\d+$']

Spread interpretation:
    Group with the largest spread reduction relative to baseline is the
    biggest absorber. Group with no spread reduction is innocent of the
    y-dependent tension we're chasing.
"""

import argparse
import re
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.stats import chi2 as _chi2

WUMS = Path("/home/submit/lavezzo/alphaS/main/WRemnants/wums")
RABBIT = Path("/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, str(WUMS))
sys.path.insert(0, str(RABBIT))

from rabbit import io_tools  # noqa: E402


def get_poi_table(path, poi_regex, min_pois=2):
    fitresult, meta = io_tools.get_fitresult(path, meta=True)
    pat = re.compile(poi_regex)
    poi_names = [str(p) for p in io_tools.get_poi_names(meta) if pat.match(str(p))]
    if len(poi_names) < min_pois:
        raise SystemExit(f"{path}: only {len(poi_names)} POIs match {poi_regex}")

    h = fitresult["parms"].get()
    labels = np.array([str(l) for l in h.axes["parms"]])
    idx = {l: i for i, l in enumerate(labels)}
    centrals = np.array([h.values()[idx[p]] for p in poi_names])
    sigmas = np.sqrt(np.array([h.variances()[idx[p]] for p in poi_names]))

    nll = None
    if "nllvalreduced" in fitresult.keys():
        try:
            nll = float(fitresult["nllvalreduced"][...])
        except Exception:
            nll = None
    nll_full = None
    if "nllvalfull" in fitresult.keys():
        try:
            nll_full = float(fitresult["nllvalfull"][...])
        except Exception:
            nll_full = None
    return poi_names, centrals, sigmas, nll, nll_full


def summarise(centrals):
    """Spread metrics that are invariant under the common blinding offset."""
    spread = float(centrals.max() - centrals.min())
    rms = float(np.std(centrals, ddof=1)) if len(centrals) > 1 else 0.0
    return spread, rms


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--baseline", required=True, help="Unfrozen decorrelated fit (reference)."
    )
    p.add_argument(
        "--frozen",
        nargs="*",
        default=[],
        metavar="GROUP=PATH",
        help="One entry per frozen-group refit, "
        "e.g. pdf_mb=/.../fitresults_freeze_pdf_mb_decorr.hdf5",
    )
    p.add_argument(
        "--inclusive",
        default=None,
        help="Optional unfrozen inclusive-alphaS fit for the full "
        "Wilks LRT against baseline.",
    )
    p.add_argument(
        "--inclusive-frozen",
        nargs="*",
        default=[],
        metavar="GROUP=PATH",
        help="Inclusive-alphaS partner refits with the same freeze "
        "groups, for the partial-LRT. e.g. "
        "pdf_mb=/.../fitresults_freeze_pdf_mb_inclusive.hdf5",
    )
    p.add_argument(
        "--poiRegex",
        default=r"^.*AlphaS.*yll_decorr\d+$",
        help="Regex matching the per-bin alphaS POIs.",
    )
    args = p.parse_args()

    poi_names0, c0, s0, nll0, nllf0 = get_poi_table(args.baseline, args.poiRegex)
    spread0, rms0 = summarise(c0)
    print(f"=== Baseline (unfrozen decorr): {args.baseline}")
    print(f"    {len(poi_names0)} POIs, NLL_red = {nll0}, NLL_full = {nllf0}")
    print(
        f"    spread = {spread0:.5g}, rms = {rms0:.5g}, "
        f"median sigma = {np.median(s0):.5g}"
    )

    if args.inclusive is not None:
        _, _, _, nlli, nlli_full = get_poi_table(
            args.inclusive,
            r".*AlphaS.*",
            min_pois=1,
        )
        ndf = len(poi_names0) - 1
        chi2v = 2.0 * (nlli - nll0) if (nlli is not None and nll0 is not None) else None
        if chi2v is not None:
            print(f"\n=== Wilks LRT (full likelihood) ===")
            print(f"    NLL_incl_red = {nlli:.4f}, NLL_decorr_red = {nll0:.4f}")
            print(f"    chi2 = 2*(NLL_inc - NLL_dec) = {chi2v:.3f}")
            print(f"    ndf  = N_POI - 1             = {ndf}")
            print(
                f"    p-value                       = "
                f"{1 - _chi2.cdf(chi2v, ndf):.3g}"
            )
        if nllf0 is not None and nlli_full is not None:
            chi2vf = 2.0 * (nlli_full - nllf0)
            print(
                f"    (full Nll) chi2 = {chi2vf:.3f}, "
                f"p = {1 - _chi2.cdf(chi2vf, ndf):.3g}"
            )

    print(f"\n=== Per-group freeze table ===")
    rows = [("baseline", "(none)", spread0, rms0, 1.0, 1.0, nll0, 0.0, nllf0, 0.0)]
    for entry in args.frozen:
        if "=" not in entry:
            print(f"WARN: skipping malformed --frozen entry '{entry}'")
            continue
        gname, path = entry.split("=", 1)
        try:
            poi_names, cg, sg, nllg, nllgf = get_poi_table(path, args.poiRegex)
        except (FileNotFoundError, OSError) as e:
            rows.append((gname, path, None, None, None, None, None, None, None, None))
            print(f"WARN: cannot read {path}: {e}")
            continue
        if list(poi_names) != list(poi_names0):
            print(f"WARN: POI list differs for group {gname}; intersection only.")
        spread, rms = summarise(cg)
        spread_ratio = spread / spread0 if spread0 > 0 else float("nan")
        rms_ratio = rms / rms0 if rms0 > 0 else float("nan")
        dnll = (nllg - nll0) if (nllg is not None and nll0 is not None) else None
        dnllf = (nllgf - nllf0) if (nllgf is not None and nllf0 is not None) else None
        rows.append(
            (
                gname,
                path,
                spread,
                rms,
                spread_ratio,
                rms_ratio,
                nllg,
                dnll,
                nllgf,
                dnllf,
            )
        )

    header = (
        "group",
        "spread",
        "rms",
        "spread/baseline",
        "rms/baseline",
        "NLL",
        "ΔNLL_red",
        "NLL_full",
        "ΔNLL_full",
    )
    widths = [22, 12, 12, 16, 14, 14, 12, 14, 12]
    fmt_row = lambda r: " ".join(str(r[i]).ljust(widths[i]) for i in range(len(r)))
    print(fmt_row(header))
    print("-" * sum(widths))
    for gname, path, spread, rms, sr, rr, nll, dnll, nllf, dnllf in rows:

        def f(x, n=5):
            if x is None:
                return "n/a"
            if isinstance(x, str):
                return x
            return f"{x:.{n}g}"

        print(
            fmt_row(
                (
                    gname,
                    f(spread),
                    f(rms),
                    f(sr, 4),
                    f(rr, 4),
                    f(nll, 5),
                    f(dnll, 4),
                    f(nllf, 5),
                    f(dnllf, 4),
                )
            )
        )

    print("\nNotes:")
    print(
        "  * spread/baseline < 1 means freezing this group reduced the "
        "y-dependent alphaS spread."
    )
    print(
        "  * ΔNLL = NLL_frozen - NLL_baseline; positive (refit got worse "
        "since fewer DoF), and the size of the increase tells you how much "
        "freedom that group was using."
    )

    # Partial-LRT: pair each frozen-decorr fit with its frozen-inclusive
    # partner and recompute chi2 inside the frozen sub-model.
    if args.inclusive_frozen:
        ndf = len(poi_names0) - 1
        # baseline LRT (unfrozen)
        chi2_full_red = chi2_full_full = None
        if args.inclusive is not None:
            _, _, _, nlli, nlli_full = get_poi_table(
                args.inclusive,
                r".*AlphaS.*",
                min_pois=1,
            )
            if nlli is not None and nll0 is not None:
                chi2_full_red = 2.0 * (nlli - nll0)
            if nlli_full is not None and nllf0 is not None:
                chi2_full_full = 2.0 * (nlli_full - nllf0)

        # decorr-frozen NLLs by group, from the rows we already built
        decorr_nll = {
            gname: (nll, nllf)
            for (gname, _, _, _, _, _, nll, _, nllf, _) in rows
            if gname != "baseline"
        }

        print("\n=== Partial-LRT: chi2 inside frozen sub-model ===")
        print(f"    ndf = N_POI - 1 = {ndf}")
        if chi2_full_red is not None:
            p_full = 1 - _chi2.cdf(chi2_full_red, ndf)
            print(
                f"    Baseline (unfrozen) LRT chi2_red = {chi2_full_red:.3f},"
                f" p = {p_full:.3g}"
            )
        if chi2_full_full is not None:
            p_fullf = 1 - _chi2.cdf(chi2_full_full, ndf)
            print(
                f"    Baseline (unfrozen) LRT chi2_full = {chi2_full_full:.3f},"
                f" p = {p_fullf:.3g}"
            )

        hdr = (
            "group",
            "chi2_red",
            "Δchi2_red",
            "chi2_full",
            "Δchi2_full",
            "p (full)",
            "spread/base",
        )
        ws = [22, 12, 12, 12, 12, 12, 12]
        prn = lambda r: " ".join(str(r[i]).ljust(ws[i]) for i in range(len(r)))
        print(prn(hdr))
        print("-" * sum(ws))

        # spread/baseline lookup
        spread_ratio = {
            gname: sr
            for (gname, _, _, _, sr, _, _, _, _, _) in rows
            if gname != "baseline"
        }

        for entry in args.inclusive_frozen:
            if "=" not in entry:
                print(f"WARN: skipping malformed --inclusive-frozen '{entry}'")
                continue
            gname, path = entry.split("=", 1)
            try:
                _, _, _, nlli_g, nlli_gf = get_poi_table(
                    path,
                    r".*AlphaS.*",
                    min_pois=1,
                )
            except (FileNotFoundError, OSError) as e:
                print(f"WARN: cannot read {path}: {e}")
                continue
            decorr = decorr_nll.get(gname, (None, None))
            nll_d, nll_df = decorr
            chi2g = (
                2.0 * (nlli_g - nll_d)
                if (nlli_g is not None and nll_d is not None)
                else None
            )
            chi2gf = (
                2.0 * (nlli_gf - nll_df)
                if (nlli_gf is not None and nll_df is not None)
                else None
            )
            dchi2 = (
                chi2g - chi2_full_red
                if (chi2g is not None and chi2_full_red is not None)
                else None
            )
            dchi2f = (
                chi2gf - chi2_full_full
                if (chi2gf is not None and chi2_full_full is not None)
                else None
            )
            pgf = (1 - _chi2.cdf(chi2gf, ndf)) if chi2gf is not None else None

            def f(x, n=4):
                if x is None:
                    return "n/a"
                return f"{x:.{n}g}"

            print(
                prn(
                    (
                        gname,
                        f(chi2g),
                        f(dchi2),
                        f(chi2gf),
                        f(dchi2f),
                        f(pgf, 3),
                        f(spread_ratio.get(gname), 4),
                    )
                )
            )

        print(
            "\nPartial-LRT interpretation " "(Δchi2 = chi2_G_frozen - chi2_unfrozen):"
        )
        print(
            "  * Δchi2 < 0 (LRT shrinks when G frozen): G was *carrying* "
            "the decorrelation preference. Freezing it removes its "
            "contribution to the LR significance."
        )
        print(
            "  * Δchi2 ≈ 0: G is innocent of the LRT preference (even if "
            "it moved the spread)."
        )
        print(
            "  * Δchi2 > 0 (LRT grows when G frozen): G was *masking* / "
            "absorbing tension; freezing it reveals more decorrelation "
            "preference. Candidate: load-bearing NP / m_b / PDF."
        )


if __name__ == "__main__":
    main()
