#!/usr/bin/env python3
"""Validation of scripts/np_functions against lattice-cs-kernel/261008-np-function-figures: byte comparison of the
two JSON outputs and a pixel diff of the four PNGs (diff maps -> repro_261008/diff/, red = differing pixel).
"""
import filecmp
import os

import numpy as np
from PIL import Image

H = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(H, "../../lattice-cs-kernel/261008-np-function-figures")
B = os.path.join(H, "repro_261008")
os.makedirs(os.path.join(B, "diff"), exist_ok=True)
for j in ("np_figs_data.json", "np_functions_values.json"):
    same = filecmp.cmp(os.path.join(A, j), os.path.join(B, "data", j), shallow=False)
    print(f"{j}: {'byte-identical' if same else 'DIFFERENT'}")
for n in (
    "cs_kernel_vs_lattice",
    "cs_kernel_full_range",
    "np_functions",
    "lambda_nu_plane",
):
    a = np.asarray(Image.open(f"{A}/{n}.png").convert("RGB")).astype(int)
    b = np.asarray(Image.open(f"{B}/{n}.png").convert("RGB")).astype(int)
    if a.shape != b.shape:
        print(f"{n}: shape {a.shape} vs {b.shape}")
        continue
    d = np.abs(a - b).sum(-1) > 0
    msg = f"{n}: {d.sum()} differing pixels ({100 * d.mean():.3f} %)"
    if d.any():
        ys, xs = np.where(d)
        msg += f", bbox x {xs.min()}-{xs.max()} y {ys.min()}-{ys.max()}"
        m = (a * 0.3).astype(np.uint8)
        m[d] = [255, 0, 0]
        Image.fromarray(m).save(f"{B}/diff/{n}_diff.png")
    print(msg)
