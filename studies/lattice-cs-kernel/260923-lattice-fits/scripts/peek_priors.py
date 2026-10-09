import sys, h5py
from wums import ioutils

meta = ioutils.pickle_load_h5py(h5py.File(sys.argv[1], "r")["meta"])
pp = meta["param_priors"]
print(type(pp), list(pp.keys())[:10] if hasattr(pp, "keys") else pp)
for k, v in pp.items():
    print(k, str(v)[:600])
