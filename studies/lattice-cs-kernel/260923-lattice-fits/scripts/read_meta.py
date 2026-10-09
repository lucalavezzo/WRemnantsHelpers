"""Print the rabbit_fit args recorded in a fitresult's meta_info."""

import sys, json
from wums import ioutils
import h5py

for f in sys.argv[1:]:
    h = h5py.File(f, "r")
    print("==", f)
    meta = ioutils.pickle_load_h5py(h["meta"])
    mi = meta.get("meta_info", meta)
    for k in ("command", "args", "git_hash", "git_diff"):
        if k in mi:
            v = mi[k]
            if k == "git_diff":
                print(k, "len", len(str(v)))
            elif k == "args":
                print("args:")
                for a, b in sorted(v.items()):
                    print(f"   {a} = {b!r}")
            else:
                print(k, "=", v)
    print("meta keys", list(meta.keys()), list(mi.keys()))
