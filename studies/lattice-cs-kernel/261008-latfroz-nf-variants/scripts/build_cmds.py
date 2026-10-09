#!/usr/bin/env python3
"""cmds/LATFROZ_V{1,2,3}.cmd from LATB8's own command (its fitresult meta_info == 261007-lattice-term-native/cmds/LATB8.cmd).
Changes, and nothing else: postfix / output dir / snapshot; the lattice term's options (syst=Jnf, pert=frozen
alphas_frozen=0.1168, the n_f variant); --externalPostfit = LATB8's fitresult (warm at its minimum, tau 8 directly, as
LATB8 itself was started from LATB5); the cache path spelled at its new location (the old path is a symlink to it).
Prints the token diff of each command vs LATB8's."""
import os
import shlex

T = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(
    os.path.dirname(T), "261007-lattice-term-native", "cmds", "LATB8.cmd"
)
A = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS"
OUT = f"{A}/261008_latfroz_nf_variants"
L8 = f"{A}/261007_lattice_term_native/fitresults_LATB8.hdf5"
FRZ = ["syst=Jnf", "offset=min", "pert=frozen", "alphas_frozen=0.1168"]
VAR = {
    "LATFROZ_V1": ["nfmatch=1.0"],
    "LATFROZ_V2": ["nfmatch=4.18", "nfswitch=1.0"],
    "LATFROZ_V3": ["nfmatch=4.18", "nfscheme=full"],
}
base = shlex.split(open(SRC).read())
for pf, nf in VAR.items():
    t = list(base)
    t[t.index("-o") + 1] = OUT
    t[t.index("--postfix") + 1] = pf
    t[t.index("--snapshotFile") + 1] = f"{OUT}/snapshot_fitresults_{pf}.hdf5"
    t[t.index("--externalPostfit") + 1] = L8
    i = t.index(
        "wremnants.postprocessing.scetlib_ad.lattice_cs_term.LatticeCSTermMapping"
    )
    assert t[i + 1 : i + 3] == ["syst=Jnf+Jbt", "offset=min"], t[i + 1 : i + 3]
    t[i + 1 : i + 3] = FRZ + nf
    t = [s.replace(f"{A}/ad_scetlib_caches/", f"{A}/scetlib_ad_caches/") for s in t]
    open(f"{T}/cmds/{pf}.cmd", "w").write(" ".join(shlex.quote(s) for s in t) + "\n")
    print(
        f"== {pf}: removed {[s for s in base if s not in t]}\n   added {[s for s in t if s not in base]}"
    )
