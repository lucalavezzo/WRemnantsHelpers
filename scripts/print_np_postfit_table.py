#!/usr/bin/env python3
"""
Print a postfit NP-parameter table from a rabbit fitresults.hdf5, using the
canonical np_param_map.json as the source of truth for theta -> physical
parameter mapping.

Usage:
    python print_np_postfit_table.py <fitresults.hdf5> [<fitresults.hdf5> ...]

Each fitresults.hdf5 produces one column in the table. Designed for sharing
postfit values across collaborators on the same fit configuration.
"""

import argparse
import json
import os
import sys

# Anchor json next to the script.
DEFAULT_PARAM_MAP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "np_param_map.json"
)


def load_param_map(path=DEFAULT_PARAM_MAP):
    with open(path) as f:
        return json.load(f)


def physical_value_and_unc(info, theta, sigma_theta):
    """Linearization-only mapping rabbit (theta, sigma) -> (param, sigma_param).

    param(theta) = nominal + max(theta, 0)*delta_up - max(-theta, 0)*delta_down
    where delta_up = Up_template - nominal, delta_down = nominal - Down_template.

    The local sigma is |slope|*sigma_theta where slope is delta_up or delta_down
    depending on sign(theta).

    Note: this does NOT account for the helper_internal_kfactor field. By convention
    the JSON encodes templates as if scale=1; if you want to include the 10x
    amplification of CS-gamma nuisances under LatticeNoConstraints, multiply
    the physical shift (param - nominal) and its sigma by the helper kfactor.
    """
    nom = float(info["nominal"])
    up = float(info["Up_template_value"])
    down = float(info["Down_template_value"])
    delta_up = up - nom
    delta_down = nom - down
    val = nom + max(theta, 0) * delta_up - max(-theta, 0) * delta_down
    slope = delta_up if theta >= 0 else delta_down
    sigma_phys = abs(slope) * sigma_theta
    return val, sigma_phys


def read_postfit_pulls(fitresults_path):
    """Read postfit theta values and uncertainties from a rabbit fitresults.hdf5.

    Returns dict: nuisance_name -> (theta, sigma_theta).
    """
    import h5py
    import numpy as np

    sys.path.insert(
        0,
        os.environ.get(
            "RABBIT_BASE", "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit"
        ),
    )
    from rabbit.io_tools import get_fitresult, get_syst_labels

    fit = get_fitresult(fitresults_path)
    parms = fit["parms"].get()
    labels = list(parms.axes["parms"])
    values = parms.values()
    variances = parms.variances()
    out = {}
    for i, name in enumerate(labels):
        out[str(name)] = (float(values[i]), float(np.sqrt(variances[i])))
    return out


def format_value(v, unc, width=8):
    if unc == 0.0:
        return f"{v:+.4f} (frozen)"
    return f"{v:+.4f} ± {unc:.4f}"


def make_table(fitresults_paths, labels=None):
    pmap = load_param_map()
    nuisances = pmap["nuisances"]
    pulls_per_fit = [read_postfit_pulls(p) for p in fitresults_paths]

    if labels is None:
        labels = [os.path.basename(os.path.dirname(p)) for p in fitresults_paths]
    if len(labels) != len(fitresults_paths):
        raise ValueError("Number of labels must match number of fitresults.")

    print()
    print("=" * 110)
    print("Postfit NP parameter table")
    print("=" * 110)
    print()

    # Header
    name_w = 38
    col_w = 30
    print(f"{'Nuisance':{name_w}s}", end="")
    for lab in labels:
        print(f" | {lab:>{col_w}s}", end="")
    print()
    print("-" * (name_w + (col_w + 3) * len(labels)))

    # Rows
    for nuis_name, info in nuisances.items():
        param = info["param_AN"]
        side = info["side"]
        nominal = info["nominal"]
        # row 1: rabbit theta pull
        print(f"{nuis_name:{name_w}s}", end="")
        for pulls in pulls_per_fit:
            t, s = pulls.get(nuis_name, (None, None))
            if t is None:
                cell = "<not present>"
            elif s == 0.0:
                cell = "FROZEN"
            else:
                cell = f"theta = {t:+.4f} ± {s:.4f}"
            print(f" | {cell:>{col_w}s}", end="")
        print()
        # row 2: physical value
        print(f"  ({side}) {param:<{name_w-7}s}", end="")
        for pulls in pulls_per_fit:
            t, s = pulls.get(nuis_name, (None, None))
            if t is None or s == 0.0:
                if t is not None and s == 0.0:
                    cell = f"= {nominal:+.4f}"
                else:
                    cell = "—"
            else:
                v, vu = physical_value_and_unc(info, t, s)
                cell = format_value(v, vu)
            print(f" | {cell:>{col_w}s}", end="")
        print()
        # row 3: deviation from nominal
        print(f"  (Δ from nominal = {nominal:+.4f})".ljust(name_w), end="")
        for pulls in pulls_per_fit:
            t, s = pulls.get(nuis_name, (None, None))
            if t is None or s == 0.0:
                cell = "—"
            else:
                v, vu = physical_value_and_unc(info, t, s)
                cell = f"Δ = {v - nominal:+.4f}"
            print(f" | {cell:>{col_w}s}", end="")
        print()
        print()

    # Also dump pdfAlphaS sigma if present
    print("-" * (name_w + (col_w + 3) * len(labels)))
    print(f"{'pdfAlphaS (POI, theta blinded)':{name_w}s}", end="")
    for pulls in pulls_per_fit:
        t, s = pulls.get("pdfAlphaS", (None, None))
        if t is None:
            cell = "—"
        else:
            # theta is blinded; pdfAlphaS sigma is already in σ_AN units.
            cell = f"σ(αS) = {s:.3f} σ_AN"
        print(f" | {cell:>{col_w}s}", end="")
    print()
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fitresults",
        nargs="+",
        help="One or more fitresults.hdf5 files (each becomes a column).",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=None,
        help="Optional column labels (one per fitresults path).",
    )
    args = parser.parse_args()
    make_table(args.fitresults, args.labels)


if __name__ == "__main__":
    main()
