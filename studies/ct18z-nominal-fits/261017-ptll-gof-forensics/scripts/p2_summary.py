#!/usr/bin/env python3
"""P2 summary: GoF and alpha_s DIFFERENCES (in sigma of the reference) for prior-inflated refits vs the reference fit.

Never prints or stores an alpha_s value: only (a_V - a_ref)/sigma_ref and sigma_V/sigma_ref (both blinding-invariant
within the same blinding family: same card names/seed, the offset cancels in the difference).
usage: p2_summary.py --ref LAT=<fitresults> --fits A0x2=<fitresults> ... --out <json>
"""
import argparse
import json

import h5py
import numpy as np
from scipy.stats import chi2
from wums import ioutils

MAP = "Project ch0 ptll"
WATCH = [
    "QCDscaleZfine_PtV15_20helicity_0_SymAvg",
    "resumFOScaleEnvSymDiff",
    "lumi",
    "mb_up",
    "weak_default",
    "horacelophotosmecoffew_FSR_Corr0",
    "QCDscaleZfine_PtV5_7helicity_0_SymAvg",
    "QCDscaleZfine_PtV9_11helicity_0_SymAvg",
]


def read(path):
    f = h5py.File(path, "r")
    r = ioutils.pickle_load_h5py(f["results"])
    P = r["parms"].get()
    names = list(P.axes[0])
    ia = names.index("alphaS")
    out = dict(
        a=float(P.values()[ia]),
        sa=float(np.sqrt(P.variances()[ia])),
        nll=float(r["nllvalreduced"]),
        ndfsat=int(r["ndfsat"]),
    )
    m = r["mappings"][MAP]
    out["q_ptll"] = float(m.get("chi2_saturated", np.nan))
    out["lin_ptll"] = float(m.get("chi2", np.nan))
    out["pulls"] = {n: float(P.values()[names.index(n)]) for n in WATCH if n in names}
    ms = r.get("minimizer_status", {})
    out["status"] = ms.get("status") if isinstance(ms, dict) else None
    if "constraints_postfit" in r:
        out["active_faces"] = [
            str(x) for x in r["constraints_postfit"].get("active", [])
        ]
    sf = m.get("saturated_fit", {})
    if sf:
        st = sf.get("minimizer_status", {})
        out["sat_status"] = st.get("status")
        out["sat_optimality"] = st.get("optimality")
    f.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--fits", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rtag, rpath = args.ref.split("=", 1)
    ref = read(rpath)
    rows = {}
    for spec in args.fits:
        tag, path = spec.split("=", 1)
        v = read(path)
        row = dict(
            q_full=2 * v["nll"],
            ndfsat=v["ndfsat"],
            p_full=chi2.sf(2 * v["nll"], v["ndfsat"]),
            dq_full=2 * (v["nll"] - ref["nll"]),
            q_ptll=v["q_ptll"],
            p_ptll=chi2.sf(v["q_ptll"], 39),
            dq_ptll=v["q_ptll"] - ref["q_ptll"],
            lin_ptll=v["lin_ptll"],
            dalpha_over_sigma_ref=(v["a"] - ref["a"]) / ref["sa"],
            sigma_ratio=v["sa"] / ref["sa"],
            pulls=v["pulls"],
            status=v.get("status"),
            sat_status=v.get("sat_status"),
            sat_optimality=v.get("sat_optimality"),
            active_faces=v.get("active_faces"),
        )
        rows[tag] = row
        print(
            f"{tag:8s} full {row['q_full']:.2f}/{row['ndfsat']} (p {100 * row['p_full']:.1f}%, d {row['dq_full']:+.2f}) | "
            f"ptll q {row['q_ptll']:.2f}/39 (p {100 * row['p_ptll']:.3f}%, d {row['dq_ptll']:+.2f}) lin {row['lin_ptll']:.1f} | "
            f"d(alpha_s)/sigma_ref {row['dalpha_over_sigma_ref']:+.3f}  sigma ratio {row['sigma_ratio']:.3f} | "
            f"status {row['status']} sat {row['sat_status']} opt {row['sat_optimality']} faces {row['active_faces']}"
        )
        print("          pulls:", {k: round(x, 2) for k, x in row["pulls"].items()})
    rows["_ref"] = dict(
        tag=rtag, q_full=2 * ref["nll"], q_ptll=ref["q_ptll"], pulls=ref["pulls"]
    )
    json.dump(rows, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
