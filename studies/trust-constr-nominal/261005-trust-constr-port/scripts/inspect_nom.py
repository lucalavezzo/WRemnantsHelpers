import h5py, numpy as np
from rabbit import io_tools

REF = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5"
fr, meta = io_tools.get_fitresult(REF, None, meta=True)
print("CMD:", meta["meta_info"]["command"])
print("git:", meta["meta_info"].get("git_hash"))
print("keys:", list(fr.keys()))
for k in fr.keys():
    v = fr[k]
    try:
        if np.ndim(v) == 0 or isinstance(v, (dict, float, int, str)):
            print(k, "=", v if "alphaS" not in str(v) else "<blinded>")
    except Exception as e:
        print(k, type(v))
h = fr["parms"].get()
names = [str(n) for n in h.axes[0]]
print("nparms", len(names), "first", names[:12])
print("lambda in vector:", [n for n in names if "lambda" in n])
