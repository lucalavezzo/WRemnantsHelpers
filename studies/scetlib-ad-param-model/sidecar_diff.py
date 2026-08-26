#!/usr/bin/env python3
"""The .shard.json a member slice writes: old builder vs new, field by field.

The call-log harness stubs the cache WRITER, so it compares the save call but
not the sidecar the same function writes beside it -- and the sidecar is what
the merge reads to reproduce the single-process member order. So diff it
directly, through the same stubs.
"""
import importlib.util
import json
import os
import sys

STUDY = "/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model"
spec = importlib.util.spec_from_file_location(
    "dpe", os.path.join(STUDY, "default_path_equivalence.py")
)
dpe = importlib.util.module_from_spec(spec)
sys.modules["dpe"] = dpe
spec.loader.exec_module(dpe)

GRID = '{"Q": [60, 120], "Y": [0, 0.25, 0.5], "qT": [20, 27, 33, 44, 100]}'
BASE = ("/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
        "scetlib_ad_caches/par_test/base.conf")
out = {}
for tag, path in (("old", dpe.OLD), ("new", dpe.NEW)):
    d = f"/tmp/sidecar_{tag}"
    os.makedirs(d, exist_ok=True)
    dpe.run(path, ["--grid-json", GRID, "--base-conf", BASE, "-o", d,
                   "--threads", "32", "--pdf-eig", "2", "--members", "0:2"], 8)
    with open(os.path.join(d, "cache.shard.json")) as f:
        out[tag] = json.load(f)
    with open(os.path.join(d, "cache.conf")) as f:
        out[tag + "_conf"] = f.read()

same = out["old"] == out["new"]
print("\nsidecar keys:", sorted(out["old"]))
for k in sorted(set(out["old"]) | set(out["new"])):
    a, b = out["old"].get(k, "<absent>"), out["new"].get(k, "<absent>")
    mark = "" if a == b else "   <-- DIFFERS"
    print(f"  {k:<12} {str(a)[:70]}{mark}")
print("\nsidecar identical:", same)
cs = out["old_conf"] == out["new_conf"]
print("generated runcard identical:", cs)
sys.exit(0 if (same and cs) else 1)
