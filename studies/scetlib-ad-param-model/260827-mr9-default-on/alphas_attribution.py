#!/usr/bin/env python3
"""WHERE in qT the alpha_s-equivalent of the transition residual comes from.

The projection is LINEAR in the residual map at fixed mask, weighting and
nuisance basis, so restricting the residual to a qT window and projecting the
restricted map decomposes the answer exactly:

    project(d) = project(d . 1_low) + project(d . 1_high)

which is what makes this an attribution rather than a re-fit. The same solve,
the same basis and the same sigma(alpha_s) as
``lowqt_nonsingular_attribution.alphas_equivalents``; that function is called
with the window-restricted map in place of ``d``.

Reads ``mr9_default_on.npz`` -- both arms from ONE cache, in ONE process -- so
nothing here re-evaluates SCETlib and nothing can drift between the arms.
"""
import os
import sys

import numpy as np

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, STUDY)
from lowqt_nonsingular_attribution import SIG_AS, alphas_equivalents  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
z = np.load(os.path.join(HERE, "mr9_default_on.npz"), allow_pickle=True)
labels = [str(x) for x in z["labels"]]
Te = z["Te"]
tr = [L for L in labels if L.startswith("transition_points")]
SPLIT = 24.0
lo = (Te[:-1] < SPLIT)                      # qT bins below the sign flip
hi = ~lo
print(f"qT split at {SPLIT:g} GeV: {lo.sum()} bins below, {hi.sum()} at/above "
      f"(edges {Te[0]:g} .. {Te[-1]:g})")


def project(dmap):
    """alpha_s-equivalent of one residual map per direction, full-bin mask."""
    zz = dict(labels=z["labels"], d=dmap, d_aligned=dmap, rr=z["rr"],
              R_as=z["R_as"], s_cen=z["s_cen"], cover=z["cover"])
    return {L: v[0] for L, v in alphas_equivalents(zz, N=1e7).items()}


def window(dmap, m):
    out = np.zeros_like(dmap)
    out[:, :, m] = np.nan_to_num(dmap[:, :, m])
    return out


d_off, d_on = np.nan_to_num(z["d_off"]), np.nan_to_num(z["d_on"])
P = {}
for tag, dm in (("off", d_off), ("on", d_on), ("on-off", d_on - d_off)):
    P[(tag, "all")] = project(dm)
    P[(tag, "lo")] = project(window(dm, lo))
    P[(tag, "hi")] = project(window(dm, hi))

print(f"\nalpha_s-equivalent, in units of sigma(alpha_s) = {SIG_AS:.2e}")
print(f"{'direction':<34}{'arm':>8}{'qT<24':>11}{'qT>=24':>11}{'total':>11}"
      f"{'lo+hi':>11}")
for L in tr:
    for tag in ("off", "on", "on-off"):
        a, b, t = (P[(tag, 'lo')][L], P[(tag, 'hi')][L], P[(tag, 'all')][L])
        print(f"{L if tag=='off' else '':<34}{tag:>8}{a/SIG_AS:>11.4f}"
              f"{b/SIG_AS:>11.4f}{t/SIG_AS:>11.4f}{(a+b)/SIG_AS:>11.4f}")
q = lambda tag, w: np.sqrt(sum(P[(tag, w)][L] ** 2 for L in tr))
print(f"\nquadrature over the {len(tr)} transition directions, in sigma(alpha_s):")
for tag in ("off", "on", "on-off"):
    print(f"  {tag:<8} qT<24 {q(tag,'lo')/SIG_AS:7.4f}   qT>=24 "
          f"{q(tag,'hi')/SIG_AS:7.4f}   all {q(tag,'all')/SIG_AS:7.4f}")
print(f"\n  on/off, all bins  {q('on','all')/q('off','all'):.3f}")
print(f"  on/off, qT<24     {q('on','lo')/q('off','lo'):.3f}")
print(f"  on/off, qT>=24    {q('on','hi')/q('off','hi'):.3f}")
