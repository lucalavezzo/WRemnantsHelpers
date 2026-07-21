#!/usr/bin/env python3
"""Purge never-submitted phantom batches from a dokan run DB.

A phantom batch: DB rows say DISPATCHED/RUNNING, but the batch was never
submitted to condor (no job.log, no exe.log in its dir) and is not in the
condor queue. Its jobs never ran and hold no results; deleting them lets the
optimizer re-plan the work. See LOGBOOK.md 07-17/07-18 notes.

Run ONLY with the controller down. Backup created by the caller
(db.sqlite.bak_20260718_purge exists). Usage:

    python3 purge_phantoms.py           # execute
    python3 purge_phantoms.py --dry-run # count only
"""

import os
import shutil
import sqlite3
import subprocess
import sys

RUN = "/scratch/submit/cms/alphaS/CMS_Z_NNLO_condor_msht20an3lo_as118_ptz5_20260714"
DRY = "--dry-run" in sys.argv

# safety: refuse to run if a controller is alive
if subprocess.run(
    ["pgrep", "-f", "nnlojet-run submit"], capture_output=True
).stdout.strip():
    sys.exit("REFUSING: nnlojet-run controller is running. Kill it first.")

# NB: the job.log filter below is the load-bearing check (condor writes job.log
# into the batch dir at submission); this condor list is belt-and-braces only.
condor = set(
    "raw/" + line.rsplit("/raw/", 1)[-1]
    for line in subprocess.run(
        ["condor_q", "-af", "Iwd"], capture_output=True, text=True, timeout=120
    ).stdout.splitlines()
    if "/raw/" in line
)

con = sqlite3.connect(f"{RUN}/db.sqlite")
db_batches = [
    r[0]
    for r in con.execute(
        "select distinct rel_path from job where mode=2 and status in (1,2) "
        "and rel_path is not null"
    )
]
phantoms = [
    b
    for b in db_batches
    if b not in condor
    and not os.path.exists(f"{RUN}/{b}/job.log")
    and not os.path.exists(f"{RUN}/{b}/exe.log")
]
print(
    f"DB active batches: {len(db_batches)}  in condor: {len(condor)}  "
    f"phantoms: {len(phantoms)}"
)

if DRY:
    for b in phantoms[:10]:
        print("  would purge:", b)
    sys.exit(0)

n_rows = 0
for b in phantoms:
    n_rows += con.execute(
        "delete from job where mode=2 and status in (1,2) and rel_path = ?", (b,)
    ).rowcount
con.commit()
n_dirs = 0
for b in phantoms:
    d = f"{RUN}/{b}"
    if os.path.isdir(d):
        shutil.rmtree(d)
        n_dirs += 1
print(
    f"deleted {n_rows} job rows across {len(phantoms)} batches; "
    f"removed {n_dirs} dirs"
)
for r in con.execute("select status, count(*) from job where mode=2 group by status"):
    st = {0: "queued", 1: "dispatched", 2: "running", 3: "done", 4: "merged"}.get(
        r[0], r[0]
    )
    print(f"  prod {st}: {r[1]}")
