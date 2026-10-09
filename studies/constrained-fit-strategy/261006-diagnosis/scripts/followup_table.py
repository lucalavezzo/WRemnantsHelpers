#!/usr/bin/env python3
"""Summarise followup/*.json into the ranked markdown table (followup_table.md + followup_summary.json)."""
import glob
import json
import os
from collections import defaultdict

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARTS = ["NOMSTIFF", "CENS03R", "C1A", "pert000", "cold000", "pert002"]
R = defaultdict(dict)
for f in glob.glob(f"{TASK}/followup/*.json"):
    d = json.load(open(f))
    R[d["label"]][d["start"]] = d


def hours(nf, nh):
    return 2 * (27 * nf + 13 * nh) / 3600.0


rows = []
for lab, per in R.items():
    if set(per) != set(STARTS):
        continue
    conv = [per[s]["E_conv"]["n_f"] if per[s]["E_conv"] else None for s in STARTS]
    tot = [per[s]["E_total"]["n_f"] for s in STARTS]
    fails = sum(c is None for c in conv)
    hrs = [hours(per[s]["E_total"]["n_f"], per[s]["E_total"]["n_hvp"]) for s in STARTS]
    tail = [t - c for t, c in zip(tot, conv) if c is not None]
    ov = per["NOMSTIFF"]["stages"][-1]["overshoot_star"]
    rows.append(
        dict(
            label=lab,
            conv=conv,
            total=tot,
            fails=fails,
            worst_h=max(hrs),
            sum_h=sum(hrs),
            max_tail=max(tail) if tail else None,
            restarts=[per[s]["restarts"] for s in STARTS],
            overshoot=ov,
        )
    )
rows.sort(key=lambda r: (r["fails"], max(r["total"])))
json.dump(rows, open(f"{TASK}/followup_summary.json", "w"), indent=1)
hdr = (
    "| recipe | "
    + " | ".join(STARTS)
    + " | fails | worst start (est. real h) | max tail after conv. | restarts (per start) | overshoot L2(2.5) [GeV²] |"
)
out = [hdr, "|" + "---|" * (len(STARTS) + 6)]
for r in rows:
    cells = [
        f"{c}/{t}" if c is not None else f"**n/c**/{t}"
        for c, t in zip(r["conv"], r["total"])
    ]
    out.append(
        f"| {r['label']} | "
        + " | ".join(cells)
        + f" | {r['fails']} | {r['worst_h']:.1f} | {r['max_tail']} | "
        + ",".join(map(str, r["restarts"]))
        + f" | {r['overshoot']:.2g} |"
    )
open(f"{TASK}/followup_table.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
