#!/usr/bin/env python3
"""Parse rabbit fit logs (trust-krylov and trust-constr) into per-iteration tables.

No cache load, no TF: pure text parsing of the live logs on ceph. Writes
logs_parsed.json in the task dir, consumed by analyze_crawl.py and the plots.

Per iteration: loss, dt (wall time since the previous callback), accepted
(trust-krylov: the loss strictly decreased; trust-constr: always reported),
and for trust-constr the KKT line (optimality, constr_violation, barrier,
tr_radius) that the rabbit trust-constr-nominal branch logs at debug level.

scipy facts used to read dt (scipy 1.18, _trustregion.py): every iteration
evaluates fun+grad ONCE at the proposed point; after a REJECTED step the next
solve reuses the same trlib subproblem object (warm Lanczos), after an
ACCEPTED step a fresh subproblem is built and its Lanczos/CG HVPs are paid. So
dt after a rejection ~ one loss+grad, dt after an acceptance ~ one loss+grad +
n_HVP * t_HVP.
"""

import json
import os
import re
import sys

C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
LOGS = {
    # trust-krylov + stiff wall (tau 8, margin 0)
    "NOMSTIFF": f"{C}/260930_stiff_wall_fits/NOMSTIFF.log",
    "XWSTIFF": f"{C}/260930_stiff_wall_fits/XWSTIFF.log",
    "XL4ZSTIFF": f"{C}/260930_stiff_wall_fits/XL4ZSTIFF.log",
    "CMR1A": f"{C}/261005_cold_min_restart/CMR1A.log",
    "CMR1B": f"{C}/261005_cold_min_restart/CMR1B.log",
    **{
        f"CENS{n}": f"{C}/261001_census_nominal/CENS{n}.log"
        for n in ["01", "02", "03", "03R", "04", "05", "06", "07", "08", "09", "10"]
    },
    # trust-constr, hard constraints
    "TCA": f"{C}/261005_trust_constr_nominal/TCA.log",
    "TCB1": f"{C}/261005_trust_constr_nominal/TCB1.log",
    "TCB2": f"{C}/261005_trust_constr_nominal/TCB2.log",
}

ANSI = re.compile(r"\x1b\[[0-9;]*m")
IT = re.compile(
    r"Iteration (\d+): loss ([-+0-9.eE]+)\s+\[dt=([0-9.]+)s elapsed=([0-9.]+)s\]"
)
TC = re.compile(
    r"trust-constr: optimality ([-+0-9.eE]+) constr_violation ([-+0-9.eE]+) "
    r"barrier ([-+0-9.eE]+) tr_radius ([-+0-9.eE]+)"
)
TIMING = re.compile(r"\[timing\] (.+?): ([0-9.]+) s")


def parse(path):
    rows, timing = [], {}
    restarts = 0
    with open(path, errors="replace") as f:
        for line in f:
            line = ANSI.sub("", line)
            m = IT.search(line)
            if m:
                it = int(m.group(1))
                if it == 0 and rows:
                    restarts += 1
                rows.append(
                    dict(
                        it=it,
                        loss=float(m.group(2)),
                        dt=float(m.group(3)),
                        elapsed=float(m.group(4)),
                        restart=restarts,
                    )
                )
                continue
            m = TC.search(line)
            if m and rows:
                rows[-1].update(
                    opt=float(m.group(1)),
                    cviol=float(m.group(2)),
                    mu=float(m.group(3)),
                    tr=float(m.group(4)),
                )
                continue
            m = TIMING.search(line)
            if m:
                timing[m.group(1)] = float(m.group(2))
    for i, r in enumerate(rows):
        prev = rows[i - 1] if i > 0 and rows[i - 1]["restart"] == r["restart"] else None
        r["gain"] = (prev["loss"] - r["loss"]) if prev else 0.0
        r["accepted"] = bool(prev is not None and r["gain"] > 0)
        r["prev_accepted"] = bool(prev is not None and prev.get("accepted", True))
    return rows, timing


def main():
    out = {}
    for name, path in LOGS.items():
        if not os.path.exists(path):
            print(f"missing {name}: {path}", file=sys.stderr)
            continue
        rows, timing = parse(path)
        out[name] = dict(path=path, rows=rows, timing=timing)
        print(f"{name:10s} {len(rows):4d} iterations  timing={timing}")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "logs_parsed.json"), "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    main()
