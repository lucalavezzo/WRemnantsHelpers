"""Probe what the card exposes about the GEN binning (for the wall's binding |Y|)."""

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)
import numpy as np  # noqa: E402
from rabbit import inputdata  # noqa: E402

indata = inputdata.FitInputData(CARD)
aux = getattr(indata, "auxiliary", None) or {}
print("auxiliary groups:", sorted(aux))
for g, bundle in aux.items():
    print(f"--- {g} ---")
    if not isinstance(bundle, dict):
        print("   not a dict:", type(bundle))
        continue
    for k in sorted(bundle):
        v = bundle[k]
        if isinstance(v, np.ndarray):
            print(f"   {k}: ndarray shape={v.shape}")
        else:
            print(f"   {k}: {v!r}")
    for name in bundle.get("gen_axes", []):
        e = np.asarray(bundle[f"edges__{name}"])
        print(f"   GEN AXIS {name}: n={len(e) - 1} min={e.min()} max={e.max()}")
print("--- channels ---")
for ch, info in indata.channel_info.items():
    print(ch, "masked=", info.get("masked"))
    for ax in info["axes"]:
        e = np.asarray(ax.edges)
        print(f"   axis {ax.name}: n={len(e) - 1} min={e.min()} max={e.max()}")
print("--- systs (first 5) ---", [str(s) for s in indata.systs[:5]])
