#!/usr/bin/env python3
"""Absolute sigma-level error per bin per arm, from the attribution JSONs."""
import json, sys, numpy as np
for f in sys.argv[1:]:
    d = json.load(open(f))
    lab = ", ".join(f"{k}={d[k]}" for k in ("x1","x2","x3") if d[k] is not None)
    R = np.asarray(d["true_resp"], float)
    bins = np.asarray(d["bins"], float)
    arms = d["arms"]
    order = [a for a in ("shipped","anl1","anl1i1","nomuf") if a in arms]
    print(f"\n=== {f}   {lab} ===")
    print("dev in units of SIGMA (arm/runcard - 1), and |dev| as % of the response")
    hdr = f"{'qT bin':>13}{'true resp':>12}"
    for a in order: hdr += f"{a:>13}{'%resp':>8}"
    print(hdr)
    for k, b in enumerate(bins):
        line = f"[{b[4]:5g},{b[5]:5g}]".rjust(13) + f"{R[k]:>+12.3e}"
        for a in order:
            dv = arms[a]["dev"][k]
            line += f"{dv:>+13.3e}" + (f"{100*dv/R[k]:>+7.1f}%" if R[k] else f"{'--':>8}")
        print(line)
    # worst and yield-blind mean over the USABLE bins (|true resp| >= 1e-4)
    ok = np.abs(R) >= 1e-4
    print(f"  usable bins (|true resp| >= 1e-4): "
          f"{[f'[{b[4]:g},{b[5]:g}]' for b, o in zip(bins, ok) if o]}")
    for a in order:
        dv = np.abs(np.asarray(arms[a]["dev"], float))
        print(f"  {a:>10}: max|dev| over usable = {dv[ok].max():.3e}   "
              f"mean|dev| = {dv[ok].mean():.3e}   "
              f"rms(%resp) = {np.sqrt(np.mean((dv[ok]/np.abs(R[ok]))**2))*100:.1f}%")
