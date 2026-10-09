import h5py, numpy as np
from wums import ioutils

C = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5"
f = h5py.File(C, "r")
m = ioutils.pickle_load_h5py(f["meta"])
print(m.keys())
ci = m["channel_info"]
print(ci)
d = f["hdata_obs"][...]
print("N_data total", d.sum())
print("procs", f["hprocs"][...])
norm = f["hnorm"][...].reshape(780, 4)
print("proc sums", norm.sum(0), norm.sum())
mi = m["meta_info"]
print(mi.get("command", "")[:3000])
