"""SATPC_NOLAT (preconditioned saturated sub-fit) vs NOLAT's own (plain) saturated sub-fit.

Reads both fitresults (blinded alpha_s: both are real data in the same blinding frame, so a difference of blinded
values is a difference of true values) and parses both logs for the per-iteration loss/time of the saturated
sub-fit, including the warm-start slack-reset detour (iterations whose loss is above the sub-fit's start loss).
Run inside the container: python compare_satpc.py
"""

import re

import numpy as np

from rabbit import io_tools

NOL = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_ct18z_nominal_fits"
VAL = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation"
)
RUNS = {
    "plain (NOLAT)": (f"{NOL}/fitresults_NOLAT.hdf5", f"{NOL}/NOLAT.log"),
    "precond (SATPC_NOLAT)": (
        f"{VAL}/fitresults_SATPC_NOLAT.hdf5",
        f"{VAL}/SATPC_NOLAT.log",
    ),
}
ITER = re.compile(
    r"Iteration (\d+): loss ([-+0-9.eE]+)\s+\[dt=([0-9.]+)s elapsed=([0-9.]+)s\]"
)
TC = re.compile(
    r"trust-constr: optimality ([0-9.eE+-]+) constr_violation ([0-9.eE+-]+) barrier ([0-9.eE+-]+)"
)


def sat_segment(logfile):
    """Iteration lines of the LAST minimisation in the log (the saturated sub-fit)."""
    lines = open(logfile, errors="replace").read().split("Perform iterative fit")
    seg = lines[-1]
    its = [
        (int(m[1]), float(m[2]), float(m[3]), float(m[4])) for m in ITER.finditer(seg)
    ]
    tcs = [(float(m[1]), float(m[2]), float(m[3])) for m in TC.finditer(seg)]
    start = re.search(r"start loss = ([-+0-9.eE]+)", seg)
    pre = re.search(r"Preconditioned .*", seg)
    hess = re.search(r"Preconditioner reference matrix .* took ([0-9.]+) s", seg)
    return dict(
        its=its,
        tcs=tcs,
        start=float(start[1]) if start else None,
        precond=pre[0] if pre else None,
        ref_hess_s=float(hess[1]) if hess else None,
        nsegments=len(lines) - 1,
    )


def parm(h, name):
    names = [n.decode() if isinstance(n, bytes) else str(n) for n in h.axes[0]]
    i = names.index(name)
    return float(h.values()[i]), float(np.sqrt(h.variances()[i]))


out = {}
for label, (fr, lg) in RUNS.items():
    res = io_tools.get_fitresult(fr)
    (mkey,) = [k for k in res["mappings"].keys() if "ptll" in k]
    mp = res["mappings"][mkey]
    sat = mp["saturated_fit"]
    st = sat["minimizer_status"]
    nll_main = float(res["nllvalreduced"])
    nll_sat = float(sat["nllvalreduced"])
    a_sat, _ = parm(sat["parms"].get(), "alphaS")
    a_main, s_main = parm(res["parms"].get(), "alphaS")
    seg = sat_segment(lg)
    o = dict(
        mapping=mkey,
        nll_main=nll_main,
        nll_sat=nll_sat,
        q=2 * (nll_main - nll_sat),
        alphaS_sat=a_sat,
        alphaS_main=a_main,
        sigma_alphaS_main=s_main,
        status=st,
        seg=seg,
    )
    its = seg["its"]
    if its:
        o["nit_log"] = its[-1][0]
        o["wall_s"] = its[-1][3]
        if seg["start"] is not None:
            above = [it for it in its if it[1] > seg["start"] + 1e-9]
            back = next((it for it in its[1:] if it[1] <= seg["start"]), None)
            o["max_detour"] = max(it[1] for it in its) - seg["start"]
            o["detour_iters"] = len(above)
            o["detour_recovered_at"] = (back[0], back[3]) if back else None
    out[label] = o
    print(f"=== {label}: {fr}")
    for k in (
        "mapping",
        "nll_main",
        "nll_sat",
        "q",
        "alphaS_main",
        "sigma_alphaS_main",
        "alphaS_sat",
        "nit_log",
        "wall_s",
        "max_detour",
        "detour_iters",
        "detour_recovered_at",
    ):
        print(f"  {k}: {o.get(k)}")
    print(
        f"  start loss {seg['start']}, segments {seg['nsegments']}, precond: {seg['precond']}, ref Hessian {seg['ref_hess_s']} s"
    )
    for k in (
        "status",
        "nit",
        "message",
        "optimality",
        "optimality_frame",
        "optimality_physical",
        "constr_violation",
        "barrier_parameter",
        "multipliers",
        "constraint_values",
        "constraint_lower_bounds",
        "constraint_upper_bounds",
        "constraint_labels",
    ):
        print(f"  {k}: {st.get(k)}")

a, b = out.values()
print("=== comparison (precond - plain)")
print(f"  dq = {b['q'] - a['q']:.3e}")
print(
    f"  d nll_main = {b['nll_main'] - a['nll_main']:.3e} (same start point: should be ~0)"
)
print(
    f"  d alphaS_sat / sigma_main = {(b['alphaS_sat'] - a['alphaS_sat']) / a['sigma_alphaS_main']:.3e}"
)
cv_a, cv_b = np.array(a["status"]["constraint_values"]), np.array(
    b["status"]["constraint_values"]
)
print(f"  max |d constraint value| = {np.max(np.abs(cv_b - cv_a)):.3e}")
for lab, ca, cb, lo, up, ma, mb in zip(
    a["status"]["constraint_labels"],
    cv_a,
    cv_b,
    a["status"]["constraint_lower_bounds"],
    a["status"]["constraint_upper_bounds"],
    a["status"]["multipliers"],
    b["status"]["multipliers"],
):
    d = min(abs(ca - lo), abs(up - ca))
    print(
        f"  {lab}: plain {ca:.6g} (dist to bound {d:.2e}, mult {ma:.3g}) | precond {cb:.6g} (mult {mb:.3g})"
    )
if "wall_s" in a and "wall_s" in b:
    print(
        f"  wall: plain {a['wall_s']:.0f} s / {a['nit_log']} it; precond {b['wall_s']:.0f} s / {b['nit_log']} it"
    )
