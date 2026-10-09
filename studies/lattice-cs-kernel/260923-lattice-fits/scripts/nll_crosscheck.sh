#!/usr/bin/env bash
# Does the CURRENT rabbit (2a59246) reproduce an OLD reference's NLL (f77f10e) at the SAME parameter vector?
# Card A (no lattice), old default fit_params (47), wall armed as in CCWALLWARM, --externalPostfit of its fitresult,
# --noFit (Hessian kept: loading an external covariance needs it allocated): evaluate only. Expect nllvalreduced == 371.43972905 (CCWALLWARMPF) if NLL definitions match.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$A/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$A/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
OUT=$A/260923_lattice_fits/nll_crosscheck
mkdir -p $OUT
W=wremnants.postprocessing.scetlib_ad.np_damping_wall
exec "$H/agent_setup.sh" --scetlib authval -- rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix XCHKWALLWARM \
  --noFit --regularizationStrength 5 -r $W.NPDampingWall $W.NPDampingMapping \
  --externalPostfit $A/260917_cc_fits_wall/fitresults_CCWALLWARMPF.hdf5 -v 4 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=64
