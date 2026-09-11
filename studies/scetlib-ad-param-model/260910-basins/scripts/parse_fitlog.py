#!/usr/bin/env python3
"""Pull the convergence/cost numbers out of a rabbit_fit log.

These live in the LOG, not the fitresult: `nit`/`nfev`/`nhev` come from scipy's
OptimizeResult, `edmval` and the two chi2 blocks from rabbit_fit.py's own INFO
lines, and the minimize() clock from its [timing] line.  The four existing arms
were transcribed by hand into ../260910-spectral-precond/scripts/compare_arms.py;
this parser exists so the fifth arm is not transcribed by hand again.

usage: parse_fitlog.py <logfile>   -> one JSON object on stdout
"""
import json
import re
import sys

ANSI = re.compile(r"\x1b\[[0-9;]*m")
txt = ANSI.sub("", open(sys.argv[1], errors="replace").read())


def one(pat, cast=float, default=None):
    m = re.search(pat, txt, re.M)
    return cast(m.group(1)) if m else default


out = {"log": sys.argv[1]}
out["fun"] = one(r"^\s+fun:\s+([-\d.eE+]+)\s*$")
out["nit"] = one(r"^\s+nit:\s+(\d+)\s*$", int)
out["nfev"] = one(r"^\s+nfev:\s+(\d+)\s*$", int)
out["nhev"] = one(r"^\s+nhev:\s+(\d+)\s*$", int)
out["status"] = one(r"^\s+status:\s+(\d+)\s*$", int)
out["message"] = one(r"^\s+message:\s+(.*?)\s*$", str)
out["minimize_s"] = one(r"fitter\.minimize\(\):\s+([\d.]+) s")
out["edm"] = one(r"edmval:\s+([-\d.eE+]+)")
# Two chi2 blocks are printed (prefit and postfit); take the LAST of each.
sat = re.findall(
    r"Saturated chi2:\s*\n\s*INFO[^\n]*ndof:\s*(\d+)\s*\n\s*INFO[^\n]*"
    r"2\*deltaNLL:\s*([-\d.]+)\s*\n\s*INFO[^\n]*p-value:\s*([\d.]+)%",
    txt,
)
if sat:
    out["sat_ndof"], out["sat_2dnll"], out["sat_p"] = (
        int(sat[-1][0]),
        float(sat[-1][1]),
        float(sat[-1][2]),
    )
lin = re.findall(
    r"Linear chi2:\s*\n\s*INFO[^\n]*ndof:\s*(\d+)\s*\n\s*INFO[^\n]*"
    r"chi2/ndf\s*=\s*([-\d.]+)\s*\n\s*INFO[^\n]*p-value:\s*([\d.]+)%",
    txt,
)
if lin:
    out["lin_ndof"], out["lin_chi2"], out["lin_p"] = (
        int(lin[-1][0]),
        float(lin[-1][1]),
        float(lin[-1][2]),
    )
    out["n_chi2_blocks"] = len(lin)
out["wall"] = one(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*([\d:.]+)", str)
out["exit_status"] = one(r"Exit status:\s*(\d+)", int)
out["maxrss_gib"] = (lambda v: round(v / 2**20, 1) if v else None)(
    one(r"Maximum resident set size \(kbytes\):\s*(\d+)", float)
)
out["load0"] = one(r"^\[run\] START[^=]*=([\d.]+)", float)
# preconditioner report, if any
m = re.search(r"condition number ([\d.eE+]+) -> ([\d.eE+]+)", txt)
if m:
    out["kappa_before"], out["kappa_after"] = float(m.group(1)), float(m.group(2))
m = re.search(r"of which degeneracy ([\d.eE+]+)", txt)
if m:
    out["degeneracy"] = float(m.group(1))
m = re.search(r"ridge from the spectrum:\s*([\d.eE+]+)", txt)
if m:
    out["ridge_frac"] = float(m.group(1))
out["n_floored"] = one(r"(\d+) floored", int)
out["armed"] = one(r"armed on (\d+) of \d+ condition", int)
# accepted/rejected trust-region steps: an iteration whose loss is bit-identical
# to the previous one is a rejected step (same counting as compare_arms.py).
losses = [float(x) for x in re.findall(r"Iteration \d+: loss ([-\d.eE+]+)", txt)]
if losses:
    rej = sum(1 for a, b in zip(losses, losses[1:]) if a == b)
    out["n_iter_logged"] = len(losses)
    out["n_rejected"] = rej
    out["frac_rejected"] = round(100.0 * rej / max(1, len(losses) - 1), 1)
    out["loss_first"], out["loss_last"] = losses[0], losses[-1]
print(json.dumps(out, indent=2))
