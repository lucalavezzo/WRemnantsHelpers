#!/usr/bin/env bash
# RETIRED 2026-10-15: scripts/np_functions/ was deleted (superseded by scetlib_ad/np_function_plots); kept as the record of the runs.
# Validation 3: trust-constr + NPDomainConstraints fitresults (face-held covariance, no wall term in the fit).
# P2B = nominal config (TMD face L2(|Y|=2.5)); P1B = the colleague's problem (CS face lambda2_nu = 0), both from
# studies/trust-constr-nominal/261013-constrained-postfit-validation. --band all=yes forces the face-held band on P1B
# to exercise sampling from a singular covariance.
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261013_constrained_postfit_validation
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
exec python3 $H/scripts/np_functions/np_functions.py \
  --fit P2B=$A/fitresults_P2B.hdf5 --fit P1B=$A/fitresults_P1B.hdf5 --band all=yes --all \
  -o $H/studies/ct18z-nominal-fits/261015-np-functions-tool/constrained_test "$@"
