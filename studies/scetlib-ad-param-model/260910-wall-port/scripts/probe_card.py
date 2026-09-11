"""Probe the card's recorded theory-correction config: NP forms + lambda anchors."""

import sys

CARD = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
    "study_scratch/260910-anchor-verify/card_none.hdf5"
)

from rabbit import inputdata  # noqa: E402

from wremnants.postprocessing.scetlib_ad import params as adp  # noqa: E402
from wremnants.postprocessing.scetlib_ad.response import (  # noqa: E402
    CORR_CONFIG_META_KEY,
    corr_config_from_meta,
)

indata = inputdata.FitInputData(CARD)
entry = corr_config_from_meta(indata.metadata or {})
print("CORR_CONFIG_META_KEY =", CORR_CONFIG_META_KEY)
print("entry keys:", None if entry is None else sorted(entry))
if entry is None:
    sys.exit("no correction config recorded")
print("tag:", entry.get("tag"), "basename:", entry.get("basename"))
print("applied_to_nominal:", entry.get("applied_to_nominal"))
cfg = entry["config"]
print("sections:", sorted(cfg))
print("--- Nonperturbative ---")
for k, v in sorted(cfg.get("Nonperturbative", {}).items()):
    print(f"  {k} = {v!r}")
print("--- anchors via params.corr_anchor_value ---")
for name in (
    "lambda2",
    "lambda4",
    "lambda6",
    "delta_lambda2",
    "lambda_inf",
    "lambda2_nu",
    "lambda4_nu",
    "lambda6_nu",
    "lambda_inf_nu",
    "b0_over_bmax_nu",
):
    print(f"  {name}: {adp.corr_anchor_value(cfg, name)!r}")
print("--- REPARAM widths ---")
for name in (
    "lambda2",
    "lambda4",
    "delta_lambda2",
    "lambda2_nu",
    "lambda4_nu",
    "lambda6",
    "lambda6_nu",
):
    print(f"  {name}: {adp.reparam(name)!r}")
print("nsyst:", indata.nsyst, "nbins:", indata.nbins)
