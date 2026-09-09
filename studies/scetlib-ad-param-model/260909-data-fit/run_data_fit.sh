#!/bin/bash
# FIT TO DATA, as-is: nothing frozen, no priors added, no NP wall.
#
# BLINDING: no --unblind, so rabbit adds an unknown shift to the alphaS POI.
# Uncertainties, pulls and impacts are meaningful; the central value is not.
#
# --earlyStopping 100: with tol=0.0 every scipy tolerance is 0 and trust-krylov
# will otherwise run to maxiter = len(x)*200, i.e. effectively forever (seen:
# 63,554 iterations over 21.8 h). 100 is the value the toys used and is well
# above the ~20 that silently aborts a healthy fit.
set -e
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$CEPH/260908_Z_2D_card_acceptfix/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
OUT=$CEPH/study_scratch/260909-data-fit
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
exec rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
  --postfix DATA -t 0 --earlyStopping 100 \
  --saveHists --computeHistErrors --doImpacts \
  --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=256
