#!/usr/bin/env python3
"""Pairwise alpha_s DIFFERENCES between the five arms, in units of sigma.

Safe under additive blinding, and only under additive blinding: rabbit 0f64bbb
stores the internal coordinate x with the SAME deterministic offset added in
every one of these fits (same card, same seedless rule), so x_a - x_b is the
offset-free physical difference even though neither x is a measurement.  No
absolute value is printed, here or anywhere in this directory.

The sigma used for a pair is the LARGER of the two postfit sigmas -- the
conservative choice, since these are not independent measurements but the same
data stopped in different minima, and a "N sigma" claim should not be inflated
by dividing through the tighter of the two.

usage: alphas_offsets.py <basins.json is not enough -- reads the fitresults>
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(HERE, "..", "..", "260910-spectral-precond", "scripts")
    ),
)
import compare_arms as CA  # noqa: E402

CA.SCRATCH = "/tmp/basins_read"
CEPH = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
WIDTH = 0.002
FITS = [
    ("plain", f"{CEPH}/260910_blinding_final/fitresults_DATABLIND.hdf5"),
    ("ridge", f"{CEPH}/260910_blinding_final/fitresults_DATAPC2.hdf5"),
    ("spectral", f"{CEPH}/260910_spectral/fitresults_DATASPECPF.hdf5"),
    ("walled", f"{CEPH}/260910_wall_port/fitresults_DATAWALL5.hdf5"),
    ("wall+ridge", f"{CEPH}/260910_basins/fitresults_DATAWALLPC.hdf5"),
]
th, sg = {}, {}
tags = []
for t, f in FITS:
    if not (os.path.exists(f) and os.path.getsize(f) > 10_000_000):
        print(f"[skip] {t}")
        continue
    n, v, e = CA.read(f)
    j = n.index("alphaS")
    th[t], sg[t] = float(v[j]) * WIDTH, float(e[j]) * WIDTH
    tags.append(t)

print()
print("=" * 84)
print("alpha_s DIFFERENCES between arms, in units of max(sigma_a, sigma_b)")
print("  (offset-free: additive blinding, same offset in every arm.")
print("   NO absolute alpha_s value is printed.)")
print("=" * 84)
print("  " + " " * 13 + "".join(t.rjust(13) for t in tags) + "   sigma(alpha_s)")
for a in tags:
    row = "".join(
        format((th[a] - th[b]) / max(sg[a], sg[b]), "+.2f").rjust(13) for b in tags
    )
    print(f"  {a:13s}{row}   {sg[a]:.6f}")
print()
sp = max(abs(th[a] - th[b]) for a in tags for b in tags)
print(
    f"  widest alpha_s spread across the five arms: {sp:.6f} in alpha_s units,"
    f"  i.e. {sp / min(sg.values()):.2f} x the tightest sigma "
    f"({min(sg.values()):.6f}) and {sp / max(sg.values()):.2f} x the loosest "
    f"({max(sg.values()):.6f})"
)
print(
    f"  sigma(alpha_s) range: {min(sg.values()):.6f} - {max(sg.values()):.6f} "
    f"({100 * (max(sg.values()) / min(sg.values()) - 1):.0f} % spread)"
)
print("ALPHAS_OFFSETS_DONE")
