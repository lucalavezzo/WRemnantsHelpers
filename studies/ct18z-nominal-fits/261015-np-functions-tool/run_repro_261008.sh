#!/usr/bin/env bash
# RETIRED 2026-10-15: scripts/np_functions/ was deleted (superseded by scetlib_ad/np_function_plots); kept as the record of the runs.
# Validation 1: the 261008 fit set, with the options that reproduce the 261008 figures.
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
exec python3 $H/scripts/np_functions/np_functions.py \
  --fit LATFROZ_V3=$A/261008_latfroz_nf_variants/fitresults_LATFROZ_V3.hdf5 \
  --fit XWSTIFF=$A/260930_stiff_wall_fits/fitresults_XWSTIFF.hdf5 \
  --fit NOMSTIFF=$A/260930_stiff_wall_fits/fitresults_NOMSTIFF.hdf5 \
  --label LATFROZ_V3='Z + lattice (LATFROZ V3)' \
  --label XWSTIFF='Z only (XWSTIFF)' \
  --label NOMSTIFF='Z + 1D lattice prior, $\lambda_4^\nu$=0 (NOMSTIFF)' \
  --all --np-fits LATFROZ_V3,XWSTIFF \
  --pg XWSTIFF=13.475287497597833 --pg-text XWSTIFF='Z vs lattice' \
  --total-note 'Z + lattice and Z only give the same product:\nthe Z data fix CS $\times$ TMD, the lattice\nmoves damping from the TMD to the CS side' \
  -o $H/studies/ct18z-nominal-fits/261015-np-functions-tool/repro_261008 "$@"
