from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

D = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/qsplit_probe_260923/t_q60_120"
core = ScetlibADXsec(f"{D}/cache.conf", f"{D}/cache.npz", threads=4, fo_muf_poly=0)
print(core.bins)
print(core.param_names)
print(core.anchor)
v, j = core.values_and_jacobian(core.anchor)
print(v)
import numpy as np

ik = core.param_names.index("scale_kappa_R")
ix = core.param_names.index("scale_x2")
print("dkR", j[:, ik] / v, "dx2", j[:, ix] / v)
