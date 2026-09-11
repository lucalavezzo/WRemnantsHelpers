#!/usr/bin/env python3
"""Build the JSON that plot_basins.py draws, and print the numeric summary.

Two blocks:

  "warm"  -- experiment 1.  For each arm, (warm restart - its own seed) divided
             by the WARM postfit sigma, parameter by parameter.  Same quantity
             and same sigma convention as ../../260908-fit-770/compare_warm.py,
             which is the authority; that tool prints the per-arm tables and
             this one only collects them for the figure and the cross-arm view.

  "basin" -- experiment 2.  The L2 distance matrix between every pair of arms
             over the model parameters with alphaS EXCLUDED (so nothing
             unblinds), and each arm's physical NP tune, resolved through the
             wall's own theta -> physical map so it is the same map the fit used.

Reads go through a /tmp copy: another session holds these fitresults with
--externalPostfit and h5py then raises BlockingIOError.

usage: build_spec.py <out.json> [wall+ridge fitresult]
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.abspath(
    os.path.join(HERE, "..", "..", "260910-spectral-precond", "scripts")
)
sys.path.insert(0, SPEC)

CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
CARD = f"{CEPH}/study_scratch/260910-anchor-verify/card_none.hdf5"

import compare_arms as CA  # noqa: E402
from rabbit import inputdata  # noqa: E402

from wremnants.postprocessing.scetlib_ad import np_damping_wall as wall  # noqa: E402

CA.SCRATCH = "/tmp/basins_read"

SEED = {
    "plain": f"{CEPH}/260910_blinding_final/fitresults_DATABLIND.hdf5",
    "ridge": f"{CEPH}/260910_blinding_final/fitresults_DATAPC2.hdf5",
    # the spectral arm was SIGTERMed while descending; its own fitresult is a
    # 44 KB stub, and DATASPECPF is the --noFit --externalPostfit readout at
    # exactly the snapshot point.  So this seed is a STOPPING POINT, not a
    # converged minimum, and is the one arm expected to move.
    "spectral": f"{CEPH}/260910_spectral/fitresults_DATASPECPF.hdf5",
    "walled": f"{CEPH}/260910_wall_port/fitresults_DATAWALL5.hdf5",
}
WARM = {
    "plain": f"{CEPH}/260910_basins/fitresults_WARMPLAIN.hdf5",
    "ridge": f"{CEPH}/260910_basins/fitresults_WARMRIDGE.hdf5",
    "spectral": f"{CEPH}/260910_basins/fitresults_WARMSPEC.hdf5",
    "walled": f"{CEPH}/260910_basins/fitresults_WARMWALL.hdf5",
}
PHYS = [
    "alphaS",
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda2_nu",
    "lambda4_nu",
    "resumScaleMuR",
    "resumScaleMuF",
    "resumTransition2",
]
WIDTH_AS = 0.002


def done(p):
    return os.path.exists(p) and os.path.getsize(p) > 10_000_000


out = {"seeds": SEED, "warm_fits": WARM, "card": CARD}

# ------------------------------------------------------------------ warm
out["warm"] = {}
print("=" * 92)
print("EXPERIMENT 1 -- warm restart shifts, in units of the WARM postfit sigma")
print("  (alphaS is BLINDED; only shifts and sigmas appear)")
print("=" * 92)
print(
    f"{'arm':10s} {'alphaS d/sig':>13s} {'max|d|/sig':>11s} {'param':>26s} "
    f"{'>0.1sig':>8s} {'>0.5sig':>8s} {'sig(as) seed':>13s} {'sig(as) warm':>13s}"
)
print("-" * 92)
for a, wp in WARM.items():
    if not (done(wp) and done(SEED[a])):
        print(f"{a:10s}   (warm fitresult not ready)")
        continue
    ns, vs, es = CA.read(SEED[a])
    nw, vw, ew = CA.read(wp)
    assert ns == nw, f"{a}: parameter layouts differ"
    dx = np.asarray(vw) - np.asarray(vs)
    sig = np.where(np.asarray(ew) > 0, np.asarray(ew), np.nan)
    pull = dx / sig
    j = ns.index("alphaS")
    k = int(np.nanargmax(np.abs(pull)))
    out["warm"][a] = dict(
        labels=ns,
        pull_all=[None if not np.isfinite(x) else float(x) for x in pull],
        pull_named={p: float(pull[ns.index(p)]) for p in PHYS if p in ns},
        alphaS=dict(
            shift_in_sigma=float(pull[j]),
            sigma_seed=float(es[j] * WIDTH_AS),
            sigma_warm=float(ew[j] * WIDTH_AS),
        ),
        max_abs=float(np.nanmax(np.abs(pull))),
        max_param=ns[k],
        n_gt_0p1=int(np.nansum(np.abs(pull) > 0.1)),
        n_gt_0p5=int(np.nansum(np.abs(pull) > 0.5)),
        n_params=len(ns),
    )
    w = out["warm"][a]
    print(
        f"{a:10s} {pull[j]:+13.5f} {w['max_abs']:11.4f} {w['max_param']:>26s} "
        f"{w['n_gt_0p1']:8d} {w['n_gt_0p5']:8d} "
        f"{w['alphaS']['sigma_seed']:13.6f} {w['alphaS']['sigma_warm']:13.6f}"
    )

# ------------------------------------------------------------------ basin
FITS = dict(SEED)
if len(sys.argv) > 2:
    FITS["wall+ridge"] = sys.argv[2]
elif done(f"{CEPH}/260910_basins/fitresults_DATAWALLPC.hdf5"):
    FITS["wall+ridge"] = f"{CEPH}/260910_basins/fitresults_DATAWALLPC.hdf5"

inp = wall.resolve_wall_inputs(inputdata.FitInputData(CARD))
conds = wall.damping_conditions(inp["np_model"], inp["np_model_nu"], inp["ymax"])
tags, theta, sigd, physd = [], {}, {}, {}
for t, f in FITS.items():
    if not done(f):
        print(f"[skip basin] {t}: not ready")
        continue
    n, v, e = CA.read(f)
    tags.append(t)
    theta[t] = {k: float(v[i]) for i, k in enumerate(n)}
    sigd[t] = {k: float(e[i]) for i, k in enumerate(n)}
    physd[t] = {
        k: (
            float(wall.physical_from_theta(inp["specs"][k], theta[t][k]))
            if k in theta[t]
            else float(inp["anchors"][k])
        )
        for k in inp["names"]
    }
keys = [k for k in theta[tags[0]] if k.startswith(CA.MODEL_PREFIXES) and k != "alphaS"]


def dist(ks):
    return [
        [float(np.linalg.norm([theta[a][k] - theta[b][k] for k in ks])) for b in tags]
        for a in tags
    ]


D = dist(keys)
# Split the same distance into the NP block and everything else. The two do not
# have to agree: an arm can share a NP tune with one cluster and a profile-scale
# / PDF tune with another, and the total L2 then hides that.
NP_KEYS = [k for k in keys if k.startswith(("lambda", "delta_lambda", "b0_over_bmax"))]
REST_KEYS = [k for k in keys if k not in NP_KEYS]
D_np, D_rest = dist(NP_KEYS), dist(REST_KEYS)
out["basin"] = dict(
    tags=tags,
    L2=D,
    n_keys=len(keys),
    fits=FITS,
    L2_np=D_np,
    L2_rest=D_rest,
    np_keys=NP_KEYS,
    n_rest=len(REST_KEYS),
    lambda_names=list(inp["names"]),
    anchors={k: float(inp["anchors"][k]) for k in inp["names"]},
    phys=physd,
    sigma_alphaS={t: sigd[t]["alphaS"] * WIDTH_AS for t in tags},
    bare_penalty={
        t: float(sum(c.penalty(physd[t], wall.numpy_relu2) for c in conds))
        for t in tags
    },
    n_violated={
        t: int(
            sum(1 for c in conds if float(c.value(physd[t], wall.numpy_relu2)) < 0.0)
        )
        for t in tags
    },
    n_conditions=len(conds),
)

print()
print("=" * 92)
print("EXPERIMENT 2 -- basin identity")
print("=" * 92)
print(f"  L2 over {len(keys)} model parameters (alphaS excluded), theta units")
print("  " + " " * 13 + "".join(t.rjust(13) for t in tags))
for i, a in enumerate(tags):
    print(
        f"  {a:13s}"
        + "".join(format(D[i][j], ".3f").rjust(13) for j in range(len(tags)))
    )
for nm, M, ks in (
    ("NP block only", D_np, NP_KEYS),
    ("everything else (scales/TNP/PDF)", D_rest, REST_KEYS),
):
    print()
    print(f"  L2 over the {len(ks)} {nm}")
    print("  " + " " * 13 + "".join(t.rjust(13) for t in tags))
    for i, a in enumerate(tags):
        print(
            f"  {a:13s}"
            + "".join(format(M[i][j], ".3f").rjust(13) for j in range(len(tags)))
        )

print()
print(f"  {'arm':13s}{'sigma(alpha_s)':>16s}{'NP viol':>10s}{'bare penalty':>15s}")
for t in tags:
    print(
        f"  {t:13s}{out['basin']['sigma_alphaS'][t]:16.6f}"
        f"{out['basin']['n_violated'][t]:>7d}/{out['basin']['n_conditions']:<2d}"
        f"{out['basin']['bare_penalty'][t]:15.6g}"
    )

json.dump(out, open(sys.argv[1], "w"))
print(f"\n[wrote {sys.argv[1]}]")
print("BUILD_SPEC_DONE")
