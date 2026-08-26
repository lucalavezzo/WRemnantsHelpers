#!/usr/bin/env python3
"""prepare_cache_for_card.py with a FIVE-KNOT muF stencil.

The knot COUNT is the only thing that differs from the upstream driver, so it
is imposed here by wrapping rather than by editing
scripts/rabbit/scetlib_ad/prepare_cache_for_card.py -- which other sessions are
using, and which would then differ between arms for reasons a reader could not
check afterwards.

MUF_NMEM (env, default 4) is the number of muF member columns:
    2  kappa_F = 1/f, 1, f            -- the shipped three-knot quadratic
    4  kappa_F = 1/f, 1/sqrt f, 1, sqrt f, f  -- the five-knot quartic
MUF_KNOT (env, default 2) is the OUTER factor f.

A cache built with 4 can be EVALUATED as either, via
DrellYan.set_muf_knots_used(2), so one build serves both arms of the A/B with
the node set, the rules, the outer member convolutions and the re-solved
weights bit-identical between them. Building two caches would not: the bT node
set is not reproducible between processes.

Everything else -- card, runcard, subset, threads, member order -- is the
upstream script's, unmodified.
"""
import importlib.util
import os
import sys

import numpy as np

SRC = (
    "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/"
    "prepare_cache_for_card.py"
)

spec = importlib.util.spec_from_file_location("pcfc_5knot", SRC)
mod = importlib.util.module_from_spec(spec)
sys.modules["pcfc_5knot"] = mod
spec.loader.exec_module(mod)

NMEM = int(os.environ.get("MUF_NMEM", "4"))
KNOT = float(os.environ.get("MUF_KNOT", "2.0"))

_orig_plan = mod.plan_variations


def plan_variations(p0, names, conf, args):
    plan = _orig_plan(p0, names, conf, args)
    if plan is None or not plan["muf_hi"]:
        return plan
    plan["muf_lo"], plan["muf_hi"] = 1.0 / KNOT, KNOT
    if NMEM == 4:
        # Two more members, AFTER the existing muF pair, so the outer knots keep
        # their slots. The kernel reads the tail as
        # [lo_out, hi_out, lo_in, hi_in] and the builder assigns the legs
        # -1, +1, -1/2, +1/2 in units of ln(f) in that same order.
        plan["pairs"].append((len(plan["members"]), len(plan["members"]) + 2,
                              "muF_inner"))
        plan["sets"] += [plan["pdf_set"], plan["pdf_set"]]
        plan["members"] += [0, 0]
    print(f"  muF STENCIL OVERRIDE: {NMEM} members, kappa_F knots at "
          f"{1.0/KNOT:g}"
          + (f", {KNOT**-0.5:.6g}, 1, {KNOT**0.5:.6g}, " if NMEM == 4 else ", 1, ")
          + f"{KNOT:g}", flush=True)
    return plan


_orig_build = mod.build_variations


def build_variations(sing, nons, bins, p0, plan, args, lo=0, hi=None):
    """The upstream member build, with muf_nmem threaded through.

    Deliberately NOT a copy of the upstream body: it calls the upstream
    function with the two C++ builders temporarily bound to partials that carry
    muf_nmem, so every other decision the upstream makes (beamfunc grids, slice
    handling, the printed provenance) stays exactly the upstream's.
    """
    if plan is None or not plan["muf_hi"]:
        return _orig_build(sing, nons, bins, p0, plan, args, lo, hi)

    real_sing = sing.build_pdf_variations
    real_nons = nons.build_fo_pdf_variations

    class _S:
        def __init__(self, o):
            self._o = o

        def __getattr__(self, k):
            return getattr(self._o, k)

    ws, wn = _S(sing), _S(nons)
    ws.build_pdf_variations = lambda *a, **kw: real_sing(
        *a, **dict(kw, muf_nmem=NMEM)
    )
    wn.build_fo_pdf_variations = lambda *a, **kw: real_nons(
        *a, **dict(kw, muf_nmem=NMEM)
    )
    return _orig_build(ws, wn, bins, p0, plan, args, lo, hi)


mod.plan_variations = plan_variations
mod.build_variations = build_variations
mod.main()
