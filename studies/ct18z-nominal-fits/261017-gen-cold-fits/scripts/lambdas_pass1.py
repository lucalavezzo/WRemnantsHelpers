"""Physical NP lambdas + active faces of the pass-1 (no covariance) gen fits. No alphaS value is read."""

from wremnants.postprocessing.scetlib_ad import np_function_plots as nfp

O = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261017_gen_nominal_fits"
for pf in ("GEN_NOLAT", "GEN_LAT"):
    nfp.read_ad_fitresult(f"{O}/fitresults_{pf}.hdf5", n_toys=0)
