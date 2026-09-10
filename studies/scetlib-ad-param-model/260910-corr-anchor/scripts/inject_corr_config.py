#!/usr/bin/env python3
"""Hack a scetlib_corr_config entry into a COPY of a datacard.

The 260908 cards were produced before the histmaker recorded the correction
config, so this is how the read side is exercised before a histmaker rerun.
Writes to --out; never touches the input.  --mutate applies one deliberate
corruption so the refuse / warn / missing-anchor branches can be checked.
"""
import argparse
import os
import pickle
import shutil
import sys

import h5py
import lz4.frame

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants")
from wremnants.postprocessing.scetlib_ad import lambda_central as lc  # noqa: E402
from wums import ioutils  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--card", required=True)
ap.add_argument("--corr", required=True)
ap.add_argument("--out", required=True)
ap.add_argument(
    "--mutate",
    default="none",
    choices=["none", "refuse", "warn", "missing", "altonly"],
)
a = ap.parse_args()

with lz4.frame.open(a.corr, "rb") as fh:
    entry = lc.extract_corr_config(pickle.load(fh), os.path.basename(a.corr), "Z")

cfg = entry["config"]
if a.mutate == "refuse":
    cfg["QCD"]["pdf_set"] = "NNPDF31_nnlo_as_0118"
elif a.mutate == "warn":
    cfg["Nonperturbative"]["lambda2"] = "0.45"
elif a.mutate == "missing":
    del cfg["Nonperturbative"]["lambda2"]
elif a.mutate == "altonly":
    entry["applied_to_nominal"] = False

os.makedirs(os.path.dirname(a.out), exist_ok=True)
if os.path.abspath(a.card) != os.path.abspath(a.out):
    shutil.copyfile(a.card, a.out)
with h5py.File(a.out, "r+") as f:
    meta = ioutils.pickle_load_h5py(f["meta"])
    # same level the histmaker's own meta_info lands at
    meta["meta_info_input"][lc.CORR_CONFIG_META_KEY] = {"Z": entry}
    del f["meta"]
    ioutils.pickle_dump_h5py("meta", meta, f)
print(f"wrote {a.out}  (mutate={a.mutate}, basename={entry['basename']})")
