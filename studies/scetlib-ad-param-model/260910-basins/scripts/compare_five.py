#!/usr/bin/env python3
"""Five-way arm comparison: the four existing basins plus walled+preconditioned.

This is NOT a new tool.  It IMPORTS ../260910-spectral-precond/scripts/compare_arms.py
-- the four-way reader written for exactly this comparison, which already knows how
to map theta -> physical lambda through the wall's own resolver, to evaluate the
damping conditions, to remove the wall penalty from a walled loss, and to compute
the L2 distance between arms over the model parameters with alphaS EXCLUDED so that
nothing unblinds -- and appends one more arm to its ARMS list.

The four existing arms keep the numbers transcribed there by hand.  Those were
independently re-derived from the same logs with scripts/parse_fitlog.py and agree
exactly (fun, nit, nfev, nhev, minimize_s, edm, saturated and linear chi2), so the
transcription is verified, not assumed.  The FIFTH arm is parsed from its log so it
is never transcribed at all.

POLICY, inherited: alphaS's central value is blinded and is never printed.  sigma,
losses, EDM, chi2 and p-values are safe under additive blinding.

usage: compare_five.py <fit_DATAWALLPC_*.log>
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.abspath(
    os.path.join(HERE, "..", "..", "260910-spectral-precond", "scripts")
)
CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"

logfile = sys.argv[1]
p = json.loads(
    subprocess.check_output(
        [sys.executable, os.path.join(HERE, "parse_fitlog.py"), logfile]
    ).decode()
)

sys.path.insert(0, SPEC)
import compare_arms  # noqa: E402

compare_arms.ARMS.append(
    dict(
        tag="wall+ridge",
        postfix="DATAWALLPC",
        fit=f"{CEPH}/260910_basins/fitresults_DATAWALLPC.hdf5",
        fun=p["fun"],
        nit=p["nit"],
        nfev=p["nfev"],
        nhev=p["nhev"],
        minimize_s=p["minimize_s"],
        edm=p["edm"],
        sat_2dnll=p.get("sat_2dnll"),
        sat_ndof=p.get("sat_ndof"),
        lin_chi2=p.get("lin_chi2"),
        lin_ndof=p.get("lin_ndof"),
        sat_p=p.get("sat_p"),
        lin_p=p.get("lin_p"),
        load0=p.get("load0"),
        wall=p.get("wall"),
        precond="ridge + wall(tau=5)",
        walled=True,
        log=os.path.relpath(logfile, os.path.dirname(HERE)),
    )
)

print(f"[fifth arm parsed from] {logfile}")
for k in (
    "fun",
    "nit",
    "nfev",
    "nhev",
    "minimize_s",
    "edm",
    "status",
    "wall",
    "exit_status",
    "maxrss_gib",
    "kappa_before",
    "kappa_after",
    "degeneracy",
    "ridge_frac",
    "n_floored",
    "armed",
    "n_rejected",
    "frac_rejected",
):
    if p.get(k) is not None:
        print(f"    {k:14s} {p[k]}")
print()

sys.argv = [sys.argv[0]]
compare_arms.main()
