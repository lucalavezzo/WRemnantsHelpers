#!/usr/bin/env python3
"""Can a FROZEN node set be shared across member-build processes?

Three modes, all on the SAME runcard and the SAME bins:

  ref     prepare + build_bin_rules + ALL members            -> reference cache
  freeze  prepare + build_bin_rules, then save               -> node-set-only cache
  member  LOAD the frozen node set, build members [lo,hi)    -> member shard

If `member` runs at all, a loaded rules blob carries what the member build
needs.  If the merge of the shards is byte-identical to `ref`, the frozen node
set is genuinely shareable and D-013 can be narrowed.
"""
import argparse
import os
import sys
import time

import numpy as np

AD = "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad"
sys.path.insert(0, AD)

import prepare_cache_for_card as pcc  # noqa: E402
from wremnants.postprocessing.scetlib_ad.xsec_backend import (  # noqa: E402
    bins_from_gen_axes,
    configure,
)


def _rss(tag):
    """VmRSS / VmHWM in MB, tagged. The memory accounting of a build process."""
    d = {}
    for line in open("/proc/self/status"):
        k, _, v = line.partition(":")
        if k in ("VmRSS", "VmHWM"):
            d[k] = int(v.split()[0]) / 1024.0
    print(f"RSS[{tag}] {d.get('VmRSS', 0):.0f} MB  (peak {d.get('VmHWM', 0):.0f} MB)",
          flush=True)
    return d.get("VmRSS", 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=("ref", "freeze", "member"))
    ap.add_argument("--runcard", required=True)
    ap.add_argument("--card", required=True)
    ap.add_argument("--subset", required=True)
    ap.add_argument("--Q-lo", type=float, default=60.0)
    ap.add_argument("--Q-hi", type=float, default=120.0)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--n-train", type=int, default=9)
    ap.add_argument("--pdf-eig", type=int, default=2)
    ap.add_argument("--as-pair", default="auto")
    ap.add_argument("--no-muf", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--grid-jobs", type=int, default=0)
    ap.add_argument("--nodeset", default=None, help="mode=member: the frozen cache")
    ap.add_argument("--members", default=None, help="mode=member: LO:HI")
    ap.add_argument("-o", "--out", required=True, help="output basename (no .npz)")
    ap.add_argument("--save-nodeset", default=None, help="mode=ref: also dump the node set first")
    args = ap.parse_args()

    gen_axes = pcc.gen_axes_from_card(args.card, False)
    conf, sigma = configure(args.runcard, args.threads)
    bins = bins_from_gen_axes(gen_axes, args.Q_lo, args.Q_hi)
    n_qt = np.asarray(gen_axes[0][1]).size - 1
    n_y = np.asarray(gen_axes[1][1]).size - 1
    ysel, qsel = (x.strip() for x in args.subset.split("/"))
    iy = list(range(n_y)) if ysel == "*" else [int(v) for v in ysel.split(",")]
    iq = list(range(n_qt)) if qsel == "*" else [int(v) for v in qsel.split(",")]
    bins = bins[[i * n_y + j for i in iq for j in iy]]
    print(f"{len(bins)} bins, mode={args.mode}, threads={args.threads}", flush=True)

    _rss("configure")
    p0 = np.asarray(sigma.gradient_central(), dtype=np.float64)
    names = list(sigma.gradient_param_names())
    sing, nons = sigma.sub_pieces()
    plan = pcc.plan_variations(p0, names, conf, args)
    if plan and plan["n_eig"]:
        sing.set_pdf_eig_params(plan["n_eig"])
        nons.set_pdf_eig_params(plan["n_eig"])
        p0 = np.asarray(sing.gradient_central(), dtype=np.float64)
    print(f"{len(p0)} parameters; {len(plan['members'])} members", flush=True)

    if args.mode in ("ref", "freeze"):
        t0 = time.time()
        m0 = sigma.prepare(bins, p0)
        print(
            f"NODESET  {(time.time()-t0)/60:.2f} min  sum {float(np.sum(m0)):.10g} pb",
            flush=True,
        )
        _rss("after prepare")
        t0 = time.time()
        info = sing.build_bin_rules(
            bins, p0, n_train=args.n_train, n_hvp=1, seed=4242,
            n_jobs=args.threads or 0,
        )
        _rss("after rules")
        nodes = [d["nodes"] for d in info]
        print(
            f"RULES    {(time.time()-t0)/60:.2f} min  nodes/bin {nodes} "
            f"resid {max(d['resid'] for d in info):.2e}",
            flush=True,
        )
    else:
        path = args.nodeset if args.nodeset.endswith(".npz") else args.nodeset + ".npz"
        t0 = time.time()
        with np.load(path, allow_pickle=False) as d:
            if not np.array_equal(np.asarray(d["bins"]), bins):
                raise SystemExit("the frozen cache was built for different bins")
            rules_blob = d["rules"].tobytes()
            # ORDER. The frozen fixed-order grid carries the OUTER (Q, Y, qT)
            # node set: paired, _ad_bin_grid takes it from the partner's
            # shared_outer_grid instead of adapting one. Load it BEFORE prepare
            # so the outer grid is the file's, not a freshly adapted one.
            nons.load_fo_cache_bytes(d["fo"].tobytes())
        print(f"LOADED fo grid  {time.time()-t0:.1f} s from {path}", flush=True)
        # The per-point bT node geometry is NOT in either blob, and
        # set_pdf_keep_nodes refuses to run without it ("neither cache is
        # populated, so there is no geometry to keep"). Repopulate it by
        # evaluating once at the reference member -- on the loaded outer grid.
        t0 = time.time()
        m0 = sigma.prepare(bins, p0)
        print(
            f"REWARM   {(time.time()-t0)/60:.2f} min  sum {float(np.sum(m0)):.10g} pb",
            flush=True,
        )
        # Rules LAST: the frozen site selection replaces whatever this process
        # would have chosen, which is the whole point.
        _rss("after rewarm")
        sing.load_bin_rules_bytes(rules_blob)
        print(f"LOADED rules  has_bin_rules={sing.has_bin_rules()}", flush=True)
        _rss("after load rules")

    if args.mode == "freeze":
        pcc.write_cache(sing, nons, bins, plan, args.out)
        return
    if args.save_nodeset:
        # mode=ref: dump the node set BEFORE any member is built, so a separate
        # loaded-node-set build can be compared against this very process's
        # serial member loop. That closes the loop the split test leaves open:
        # does the rewarm reproduce the in-memory bT geometry?
        pcc.write_cache(sing, nons, bins, plan, args.save_nodeset)

    lo, hi = (0, None)
    if args.members:
        lo, hi = (int(x) for x in args.members.split(":"))
        hi = pcc.check_member_range(plan, lo, hi)
    t0 = time.time()
    pcc.build_variations(sing, nons, bins, p0, plan, args, lo, hi)
    print(f"MEMBERS  {(time.time()-t0)/60:.2f} min", flush=True)
    _rss("after members")
    pcc.write_cache(
        sing, nons, bins, plan, args.out,
        *((lo, hi) if args.members else (None, None)), args=args,
    )


if __name__ == "__main__":
    main()
