#!/usr/bin/env python3
"""Print the structure of a rabbit fitresult and the saturated-projection sub-fit status.
Run in the container: agent_setup.sh -- python3 inspect_fitresult.py <fitresults.hdf5> [--keys]
"""
import sys, numpy as np
from wums import ioutils
import h5py

path = sys.argv[1]
f = h5py.File(path, "r")
res = ioutils.pickle_load_h5py(f["results"])


def show(d, pre="", depth=0):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict) and depth < 5:
                print(pre + str(k) + "/")
                show(v, pre + "  ", depth + 1)
            else:
                t = type(v).__name__
                s = ""
                try:
                    if hasattr(v, "get"):
                        h = v.get()
                        s = f" hist axes={[a.name for a in h.axes]} shape={h.shape}"
                except Exception as e:
                    s = f" ({e})"
                if isinstance(v, (int, float, str, np.floating)):
                    s = f" = {v}"
                print(pre + str(k) + f" [{t}]" + s)


show(res)
