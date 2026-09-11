#!/usr/bin/env python3
"""What does the card already say about the NP sector?

Three questions that decide whether a lattice prior is even well posed here:

1. WHAT ARE THE ANCHORS?  The AD model fits theta with
   physical = anchor + width*theta, and the anchor comes from the card's
   recorded theory-correction runcard (params.CORR_ANCHOR_KEYS).  A prior
   written in physical lambda has to be pushed through that map, so the anchor
   is the first number to pin down -- and whether it IS the lattice central
   decides the double-counting question.

2. IS THE LATTICE CONSTRAINT ALREADY IN THE CARD?  Two ways it could be:
   template nuisances (scetlibNP* / *Lattice*) carrying their own Gaussian
   constraints, or an existing external_terms group.  Either one would make an
   added prior a double count.

3. WHAT PRIOR DOES THE MODEL ITSELF ALREADY PUT ON THE LAMBDAS?  priors
   defaults to True, so lambda2_nu already carries N(anchor, width) unless it
   is explicitly freed.
"""
import sys

import h5py
import numpy as np

CARD = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/study_scratch/260910-anchor-verify/card_none.hdf5"

from rabbit import inputdata  # noqa: E402

from wremnants.postprocessing.scetlib_ad import params as adp  # noqa: E402
from wremnants.postprocessing.scetlib_ad import response  # noqa: E402
from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

card = sys.argv[1] if len(sys.argv) > 1 else CARD
print(f"[card] {card}")

# ---- 3: raw h5 groups (external terms) -------------------------------------
with h5py.File(card, "r") as f:
    print(f"[h5] top-level groups: {sorted(f.keys())}")
    ext = f.get("external_terms")
    if ext is None:
        print("[h5] external_terms: ABSENT -> no external likelihood term on this card")
    else:
        print(f"[h5] external_terms PRESENT: {sorted(ext.keys())}")
        for k in ext:
            print(
                f"       {k}: params={[s.decode() if isinstance(s,bytes) else s for s in ext[k]['params'][...]]}"
            )

indata = inputdata.FitInputData(card)
systs = np.asarray(indata.systs).astype(str)
print(f"[card] {len(systs)} systematics")

# ---- 2: NP / lattice template nuisances ------------------------------------
pat = ("scetlibNP", "Lattice", "lattice", "Lambda", "lambda", "gamma")
hits = sorted({s for s in systs if any(p in s for p in pat)})
print(f"[card] NP-ish nuisance names ({len(hits)}):")
for h in hits[:40]:
    print(f"       {h}")
if not hits:
    print("       (none -- the NP sector is carried ONLY by the param model)")

# also: is any of them CONSTRAINED?
cw = np.asarray(indata.constraintweights)
nconstr = int((cw > 0).sum())
print(f"[card] {nconstr}/{len(cw)} card nuisances carry a Gaussian constraint")

# ---- 1: the correction's recorded runcard ----------------------------------
entry = response.corr_config_from_meta(getattr(indata, "metadata", None) or {})
print(
    f"[corr] recorded correction tag: {entry.get('tag')!r} "
    f"basename {entry.get('basename')!r}"
)
cfg = entry["config"]
npsec = cfg.get("Nonperturbative", {})
print("[corr] Nonperturbative section of the recorded correction runcard:")
for k in sorted(npsec):
    print(f"       {k:28s} {npsec[k]}")

print("[anchor] params.corr_anchor_value on that config:")
for n in (
    "lambda2",
    "lambda4",
    "lambda6",
    "delta_lambda2",
    "lambda_inf",
    "lambda2_nu",
    "lambda4_nu",
    "lambda6_nu",
    "lambda_inf_nu",
):
    try:
        a = adp.corr_anchor_value(cfg, n)
    except Exception as ex:  # noqa: BLE001
        a = f"<{type(ex).__name__}: {ex}>"
    rp = adp.reparam(n)
    w = rp[1][0] if rp and rp[0] == "unit" else None
    free = n in adp.FREE_PARAMS
    frozen = n in adp.DEFAULT_FROZEN
    print(
        f"       {n:16s} anchor={a!s:>12}  width={w!s:>6}  "
        f"{'FREE' if free else 'sigma=1'}{'  DEFAULT_FROZEN' if frozen else ''}"
    )

inp = wall.resolve_wall_inputs(indata)
print(
    f"[wall] forms np_model={inp['np_model']} np_model_nu={inp['np_model_nu']} "
    f"ymax={inp['ymax']} from {inp['ymax_source']}"
)
print("[wall] specs (the theta->physical map the wall and the model share):")
for n in inp["names"]:
    print(f"       {n:16s} spec={inp['specs'][n]}  anchor={inp['anchors'][n]}")
print("PROBE_DONE")
