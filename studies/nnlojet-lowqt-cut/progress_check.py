#!/usr/bin/env python3
"""Read-only progress snapshot of a dokan NNLOJET run: CPU-h, job counts, per-part accuracy.

Usage: python3 progress_check.py [RUN_DIR]
Safe to run anytime (RO sqlite + glob); works on the login node.
"""

import glob
import sqlite3
import sys

RUN = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714"
)

con = sqlite3.connect(f"file:{RUN}/db.sqlite?mode=ro", uri=True)

n_coll, cpuh_coll, mean_h = list(
    con.execute(
        "select count(*), sum(elapsed_time)/3600.0, avg(elapsed_time)/3600.0 "
        "from job where mode=2 and status in (3,4) and elapsed_time is not null"
    )
)[0]
n_disk = len(glob.glob(f"{RUN}/raw/production/*/s*/ZJ.CMS_Z.*.cross.s*.dat"))
cpuh_est = n_disk * (mean_h or 0)
print(f"finished jobs on disk : {n_disk}  (collected into DB: {n_coll})")
print(f"CPU-h collected       : {cpuh_coll or 0:9.0f}")
print(
    f"CPU-h est. total spent: {cpuh_est:9.0f}  (disk count x mean {mean_h or 0:.2f} h)"
)

print("\nper-part rel. error of the incremental merge (worst 12, target 1%):")
rows = [
    (n, T / 3600.0, abs(e / r) * 100 if r else float("inf"))
    for n, T, r, e in con.execute(
        "select name, Ttot, result, error from part where active=1 and result != 0"
    )
]
for n, T, rel in sorted(rows, key=lambda x: -x[2])[:12]:
    print(f"  {n:9s} T={T:7.0f} CPU-h  rel_err={rel:8.2f}%")
done_1pct = sum(1 for _, _, rel in rows if rel <= 1.0)
print(f"\nparts at/below 1%: {done_1pct}/{len(rows)}")
print(
    "NB: incremental-merge errors steer the optimizer; blessed numbers come "
    "from `finalize` (k-scan calibration may enlarge errors — see logbook)."
)
