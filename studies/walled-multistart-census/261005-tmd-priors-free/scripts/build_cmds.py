#!/usr/bin/env python3
"""Build the NOMTMDFREE command from NOMSTIFF's OWN meta_info command (pattern: 261001-census-nominal/scripts/build_cmds.py).

Changes ONLY: -o, --postfix NOMTMDFREE, --snapshotFile, --externalPostfit <NOMSTIFF fitresult>,
--earlyStopping 100 -> 20 (census convention), and the param-model token
  prior_sigmas=lambda2_nu=nan -> prior_sigmas=lambda2_nu=nan,lambda2=nan,lambda4=nan,delta_lambda2=nan
(nan = free, SCETlibADParamModel._setup_priors). The lattice term on lambda2_nu lives in the CARD
(cardA_latticeASWZ_l4zero_statsyst.hdf5), not in prior_sigmas, so it is untouched.
Writes cmds/NOMTMDFREE.cmd; prints the token diff.
"""
import difflib
import os
import shlex

from rabbit import io_tools

A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
REF = f"{A}/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
OUT = f"{A}/261005_tmd_priors_free"
TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PF = "NOMTMDFREE"

_, meta = io_tools.get_fitresult(REF, None, meta=True)
toks = shlex.split(meta["meta_info"]["command"])
new = list(toks)


def setval(flag, val, old=None):
    i = new.index(flag)
    assert new.count(flag) == 1, flag
    if old is not None:
        assert new[i + 1] == old, (flag, new[i + 1])
    new[i + 1] = val


setval("-o", OUT)
setval("--postfix", PF, old="NOMSTIFF")
setval("--snapshotFile", f"{OUT}/snapshot_fitresults_{PF}.hdf5")
setval("--externalPostfit", REF)
setval("--earlyStopping", "20", old="100")
ip = [i for i, t in enumerate(new) if t.startswith("prior_sigmas=")]
assert len(ip) == 1 and new[ip[0]] == "prior_sigmas=lambda2_nu=nan", [
    new[i] for i in ip
]
new[ip[0]] = "prior_sigmas=lambda2_nu=nan,lambda2=nan,lambda4=nan,delta_lambda2=nan"
# sanity: configuration otherwise untouched
assert new[new.index("--regularizationStrength") + 1] == "8"
r = new.index("-r")
assert new[r + 3] == "margin=0", new[r : r + 4]
assert "cardA_latticeASWZ_l4zero_statsyst.hdf5" in new[1]
assert any("pdf62_y35_260921/merged_full_bin0xzero/cache.npz" in t for t in new)
assert "--noFit" not in new and "--unblind" not in new and "-m" not in new
assert "--doImpacts" not in new and "--computeSaturatedProjectionTests" not in new
os.makedirs(f"{TASK}/cmds", exist_ok=True)
with open(f"{TASK}/cmds/{PF}.cmd", "w") as fh:
    fh.write(" ".join(shlex.quote(t) for t in new) + "\n")
print(f"=== {PF}")
for d in difflib.unified_diff(toks, new, lineterm="", n=0):
    if d.startswith(("+", "-")) and not d.startswith(("+++", "---")):
        print("   ", d)
