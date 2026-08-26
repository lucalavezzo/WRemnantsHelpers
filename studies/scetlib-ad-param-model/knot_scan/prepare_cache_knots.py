#!/usr/bin/env python3
"""prepare_cache_for_card.py with the muF knot spacing overridden.

The knot spacing is the ONLY thing that differs between the two arms of the
interpolation test, so it is imposed here rather than by editing
prepare_cache_for_card.py -- which other sessions are using, and which would
then differ between the arms for reasons a reader could not check.

MUF_KNOT (env, default 2) sets the muF member pair to kappa_F = 1/f, 1, f.
scetlib-cms's build_pdf_variations reads muf_hi and drives Scale_provider's
Vary.muf factor from it, so this one number moves the MEMBERS and the
interpolation variable t = ln(kappa_F)/ln(f) together.

Everything else -- card, runcard, subset, threads, member order -- is the
upstream script's, unmodified.
"""
import importlib.util
import os
import sys

SRC = (
    "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/"
    "prepare_cache_for_card.py"
)

spec = importlib.util.spec_from_file_location("pcfc_knots", SRC)
mod = importlib.util.module_from_spec(spec)
sys.modules["pcfc_knots"] = mod
spec.loader.exec_module(mod)

_orig_plan = mod.plan_variations


def plan_variations(p0, names, conf, args):
    plan = _orig_plan(p0, names, conf, args)
    f = float(os.environ.get("MUF_KNOT", "2.0"))
    if plan is not None and plan["muf_hi"]:
        plan["muf_lo"], plan["muf_hi"] = 1.0 / f, f
        print(f"  muF KNOT SPACING OVERRIDE: kappa_F = {1.0/f:.6f} / 1 / {f:.6f}",
              flush=True)
    return plan


mod.plan_variations = plan_variations
mod.main()
