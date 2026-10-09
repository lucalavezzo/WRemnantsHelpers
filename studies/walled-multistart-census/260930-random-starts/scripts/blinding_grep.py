#!/usr/bin/env python3
"""Blinding check of every TEXT output in the task dir (csv, log, md, py, php, txt, png/pdf metadata).

Looks for (a) the blinded alphaS x of the reference and of every seed, in repr and in
%.3f..%.10f / %.3g..%.10g renderings with >= 4 significant digits, (b) any number in [0.100, 0.135] with >= 3 decimals
on a line that mentions alphaS / alpha_s, (c) calls that would disarm/read offsets in the
scripts. Prints only counts and file names -- never a value.
"""
import glob, os, re, sys
import h5py, numpy as np
from rabbit import io_tools

task = sys.argv[1]
refs = sys.argv[2:]
vals = []
for r in refs:
    h = io_tools.get_fitresult(r, None)["parms"].get()
    names = np.array(h.axes["parms"]).astype(str)
    vals.append(float(h.values()[list(names).index("alphaS")]))
for p in glob.glob(f"{task}/**/*.hdf5", recursive=True):
    with h5py.File(p) as f:
        n = f["parms"][...].astype(str)
        vals.append(float(f["x"][...][list(n).index("alphaS")]))
pats = set()
for v in vals:
    pats.add(repr(v))
    for k in range(3, 11):
        pats.add(f"{v:.{k}f}")
        pats.add(f"{v:.{k}g}")


# >= 4 significant digits: a 3-digit rendering (e.g. "1.5") collides with bin-edge printouts
def _sig(p):
    return len(p.lstrip("-").replace(".", "").lstrip("0"))


pats = {p for p in pats if _sig(p) >= 4}
text_ext = (".csv", ".log", ".md", ".py", ".php", ".txt", ".sh", ".json")
files = [
    p
    for p in glob.glob(f"{task}/**/*", recursive=True)
    if os.path.isfile(p) and not p.endswith(".hdf5")
]
hits_a = hits_b = 0
rx_num = re.compile(r"(?<![\d.])0\.1(?:[0-2]\d|3[0-5])\d+")
for p in files:
    try:
        b = open(p, "rb").read()
    except Exception:
        continue
    s = b.decode("latin-1")
    for pat in pats:
        if pat in s:
            hits_a += 1
            print(f"  [a] blinded-x rendering found in {os.path.relpath(p, task)}")
            break
    if p.endswith(text_ext):
        for line in s.splitlines():
            if (
                re.search(r"alpha_?s", line, re.I)
                and rx_num.search(line)
                and "alphaS=" not in line.split("#")[0][:0]
            ):
                # report only file + the matched token's position, never the number
                hits_b += 1
                print(
                    f"  [b] alphaS line with a 0.10-0.135 number in {os.path.relpath(p, task)}"
                )
                break
bad_calls = []
for p in [
    q for q in glob.glob(f"{task}/scripts/*.py") if not q.endswith("blinding_grep.py")
]:
    src = open(p).read()
    # arming (blind=True) is what the fit itself does; flag only disarming / reading offsets
    for tok in (
        "set_blinding_offsets(False",
        "set_blinding_offsets(blind=False",
        "offsets_poi_add",
        "offsets_theta",
        "--unblind",
        "_arm(False",
        "_arm(blind=False",
    ):
        for line in src.splitlines():
            if (
                tok in line
                and not line.strip().startswith("#")
                and "for tok in" not in line
            ):
                bad_calls.append((os.path.basename(p), tok))
print(
    f"[blinding] {len(vals)} blinded alphaS x values checked against {len(files)} non-hdf5 files"
)
print(f"[blinding] (a) blinded-x renderings found: {hits_a}")
print(f"[blinding] (b) alphaS lines with a number in [0.100,0.135]: {hits_b}")
print(f"[blinding] (c) offset-touching calls in scripts: {bad_calls or 'none'}")
