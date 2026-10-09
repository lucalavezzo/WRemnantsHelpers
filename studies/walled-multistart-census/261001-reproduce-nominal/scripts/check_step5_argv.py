#!/usr/bin/env python3
"""No-cache check that scripts/step5_fit.sh IS the NOMSTIFF command.

Runs step5_fit.sh with STEP5_PYTHON pointed at a stub that dumps its argv, parses that argv AND the
command stored in fitresults_NOMSTIFF.hdf5 meta_info with rabbit_fit's own parser, and compares every
resulting option. Only the run-local options (-o, --postfix, --snapshotFile, --externalPostfit) may
differ. Nothing is loaded, nothing about alphaS is read. Run inside the container.
"""
import json, os, shlex, subprocess, sys, tempfile

sys.path.insert(0, os.path.join(os.environ["WREM_BASE"], "rabbit", "bin"))
import rabbit_fit  # noqa: E402
from rabbit import io_tools  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
SEED = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260928_lattice_y35_fits/fitresults_LATL4ZY35WALLWARM.hdf5"
RUN_LOCAL = {"outpath", "postfix", "snapshotFile", "externalPostfit"}

with tempfile.TemporaryDirectory() as td:
    stub = os.path.join(td, "dump")
    out = os.path.join(td, "argv.json")
    with open(stub, "w") as f:
        f.write(
            f"#!/usr/bin/env python3\nimport json,sys\njson.dump(sys.argv[1:], open({out!r},'w'))\n"
        )
    os.chmod(stub, 0o755)
    env = dict(os.environ, STEP5_PYTHON=stub)
    subprocess.run(
        [os.path.join(HERE, "step5_fit.sh"), os.path.join(td, "o"), "CHECK", SEED],
        env=env,
        check=True,
    )
    mine = json.load(open(out))[1:]  # drop the rabbit_fit.py path

_, meta = io_tools.get_fitresult(REF, None, meta=True)
ref = shlex.split(meta["meta_info"]["command"])[1:]
p = rabbit_fit.make_parser()
a, b = vars(p.parse_args(mine)), vars(p.parse_args(ref))
bad = []
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        tag = "run-local" if k in RUN_LOCAL else "DIFFERS"
        print(f"  {tag:9s} {k}: step5={a.get(k)!r}  NOMSTIFF={b.get(k)!r}")
        if k not in RUN_LOCAL:
            bad.append(k)
print(
    "RESULT:",
    "IDENTICAL apart from run-local options" if not bad else f"MISMATCH in {bad}",
)
sys.exit(1 if bad else 0)
