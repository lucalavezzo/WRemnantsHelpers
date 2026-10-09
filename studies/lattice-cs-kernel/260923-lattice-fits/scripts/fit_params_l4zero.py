"""Print the reference arms' fitted SCETlib parameter list minus lambda4_nu (comma-joined).
Envelope nuisances (resumFOScaleEnv*) are not SCETlib parameters and are added by the model itself.
"""

import sys, h5py
from wums import ioutils

meta = ioutils.pickle_load_h5py(h5py.File(sys.argv[1], "r")["meta"])
names = [p.decode() for p in meta["param_priors"]["params"]]
keep = [n for n in names if not n.startswith("resumFOScaleEnv") and n != "lambda4_nu"]
sys.stderr.write(
    f"reference has {len(names)} model params; fit_params -> {len(keep)}\n"
)
print(",".join(keep))
