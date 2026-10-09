#!/usr/bin/env python3
"""b_T reach of the NOMINAL y35 SCETlib-AD cache's compressed rules (the one cache load of this task).

Same introspection as walled-two-minima/260930-gen-xsec-lambda-scan/scripts/gen_scan.py --rules (which measured the OLD
260827 cache: largest site b_T 11-12.6 GeV^-1 for qT < 1.5): export_bin_rule gives each low-qT bin's compressed sites
(outer point, bT node, weight); export_node_grid at the cache ANCHOR gives each outer point's adapted bT nodes, so
bT(site) = nI_bT[point, node]. No parameter point other than the anchor is evaluated; alphaS is never read or printed.
Writes the per-bin reach to <task>/cache_breach.json and the raw arrays to ceph.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants")
from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec  # noqa: E402

CACHE = "/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261006_constrained_fit_diagnosis/cache_breach_rules.npz"

t0 = time.time()
core = ScetlibADXsec(f"{CACHE}/cache.conf", f"{CACHE}/cache.npz", threads=32)
print(
    f"cache constructed in {time.time()-t0:.0f} s; bins {core.bins.shape}", flush=True
)
sel = np.where(core.bins[:, 5] <= 10.0 + 1e-9)[0]
sing = core._fn._sing
rules = sing.export_bin_rule(np.ascontiguousarray(core.bins[sel]))
R, rows = dict(sel=sel, bins=core.bins[sel]), []
for ib, r in zip(sel, rules):
    g, s = np.asarray(r["grid"]), np.asarray(r["sites"])
    ex = sing.export_node_grid(
        np.ascontiguousarray(g[:, :3]), np.ascontiguousarray(core.anchor)
    )
    bT, wn = np.asarray(ex["nI_bT"]), np.asarray(ex["nI_w"])
    nreal = (wn != 0).sum(axis=1)
    pt, nd, ps = s[:, 0].astype(int), s[:, 1].astype(int), s[:, 2].astype(int)
    ok = (nd < nreal[pt]) & (ps == 0)
    siteb = np.where(ok, bT[pt, np.minimum(nd, bT.shape[1] - 1)], np.nan)
    R[f"siteb_{ib}"] = siteb
    b = core.bins[ib]
    rows.append(
        dict(
            bin=int(ib),
            Y=[float(b[2]), float(b[3])],
            qT=[float(b[4]), float(b[5])],
            n_sites=int(len(s)),
            idx_ok=float(ok.mean()),
            site_bT_max=float(np.nanmax(siteb)),
            site_bT_p99=float(np.nanpercentile(siteb, 99)),
            node_bT_max=float(np.max(bT)),
        )
    )
    print(rows[-1], flush=True)
np.savez(OUT, **R)
json.dump(
    dict(cache=CACHE, rows=rows), open(f"{TASK}/cache_breach.json", "w"), indent=1
)
print("done", flush=True)
