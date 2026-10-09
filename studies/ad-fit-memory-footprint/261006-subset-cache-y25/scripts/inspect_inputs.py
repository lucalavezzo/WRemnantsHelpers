#!/usr/bin/env python3
"""Inspect the inputs: NOMSTIFF's meta_info command (cache/conf paths), the card's gen |Y| axes
(response auxiliary), and the source cache's bins. Prints no fitted parameter values (blinded).
"""
import shlex, sys, zipfile
import h5py, numpy as np
from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
NOM = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
SRC = "/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero/cache.npz"
fr, meta = io_tools.get_fitresult(NOM, None, meta=True)
cmd = meta["meta_info"]["command"]
toks = shlex.split(cmd)
print(
    "NOMSTIFF command tokens with cache=/conf=:",
    [t for t in toks if t.startswith(("cache=", "conf="))],
)
card = toks[1]
print("card:", card)
print("fitresult keys:", sorted(k for k in fr.keys()))
with h5py.File(card, "r") as f:

    def walk(name, obj):
        if "aux" in name.lower() or "absY" in name or "gen_axes" in name:
            print("  h5:", name, getattr(obj, "shape", ""))

    f.visititems(walk)
from rabbit import inputdata

indata = inputdata.FitInputData(card)
aux = getattr(indata, "auxiliary", None) or {}
for g, b in aux.items():
    if not isinstance(b, dict):
        print("aux", g, type(b))
        continue
    print("aux group", g, "gen_axes", b.get("gen_axes"))
    for n in b.get("gen_axes", []) or []:
        e = b.get(f"edges__{n}")
        print(f"   {n}: {None if e is None else np.asarray(e).tolist()}")
for ch, info in (getattr(indata, "channel_info", None) or {}).items():
    print(
        "channel",
        ch,
        [(getattr(a, "name", ""), len(a.edges)) for a in info.get("axes", [])],
    )
with np.load(SRC) as d:
    b = d["bins"]
print(
    "cache bins",
    b.shape,
    "Y edges lo:",
    sorted(set(b[:, 2].tolist())),
    "hi max",
    b[:, 3].max(),
    "Q",
    sorted(set(b[:, 0].tolist())),
    sorted(set(b[:, 1].tolist())),
)
print(
    "n with Yhi<=2.5:",
    int((b[:, 3] <= 2.5 + 1e-12).sum()),
    " qT lo first rows:",
    b[:20, 4].tolist(),
)
