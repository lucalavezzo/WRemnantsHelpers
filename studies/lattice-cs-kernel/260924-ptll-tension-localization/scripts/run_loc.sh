#!/usr/bin/env bash
# Localisation of the ptll projected-saturated tension of LATL4ZWALLCOLD (81/39).
# Evaluates the converged LATL4ZWALLCOLD postfit (--externalPostfit, --noFit) with the SAME card, model args and wall,
# and runs rabbit's projected saturated test on the given mapping(s). No main refit: every sub-fit is warm-started
# from the loaded postfit by rabbit itself.
#   run_loc.sh <TAG> -m <mapping...> [-m <mapping...>]
set -uo pipefail
TAG=$1; shift
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_corrgrid_260827/merged_full  # scratch mirror of the ceph cache, md5-identical, faster reads
CARD=$A/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5
POST=$A/260923_lattice_fits/l4zero_walled/fitresults_LATL4ZWALLCOLD.hdf5
OUT=$A/260924_ptll_tension_loc/$TAG
FP=$(grep -o -m1 "fit_params=[^ ]*" /ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/l4zero_walled/fit_LATL4ZWALLCOLD.log | sed "s/^fit_params=//")
W=wremnants.postprocessing.scetlib_ad.np_damping_wall
mkdir -p $OUT
# half-machine budget: 64 threads per process
export OMP_NUM_THREADS=64 TF_NUM_INTRAOP_THREADS=64 TF_NUM_INTEROP_THREADS=2
"$H/agent_setup.sh" --scetlib authval -- rabbit_fit.py $CARD --jitCompile off -o $OUT -t 0 --postfix $TAG \
  --noFit --externalPostfit $POST --saveHists --computeSaturatedProjectionTests "$@" \
  --regularizationStrength 5 -r $W.NPDampingWall $W.NPDampingMapping \
  --snapshotFile $OUT/snapshot_$TAG.hdf5 --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel cache=$CACHE/cache.npz conf=$CACHE/cache.conf \
  threads=64 fit_params=$FP prior_sigmas=lambda2_nu=nan -v 4 --earlyStopping 100 2>&1 | tee -a $OUT/fit_$TAG.log
