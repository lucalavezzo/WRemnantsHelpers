#!/bin/bash
# Blinded data fit with the lattice CS-kernel constraint as a rabbit EXTERNAL
# LIKELIHOOD TERM, in the model's theta coordinate.
#
# IDENTICAL to the plain DATABLIND arm and the walled DATAWALL5 arm in every
# other respect -- same cache, same SCETlib b66f8de, same rabbit
# (blinding-additive @ 0f64bbb, asserted by incontainer.sh), real data -t 0,
# --earlyStopping 100, threads=128 -- so loss / EDM / p-values are comparable.
# Two differences, both deliberate and both part of the measurement:
#
#  1. CARD. card_latticeCS.hdf5 is card_none.hdf5 plus one external_terms group
#     (scripts/inject_lattice_cs_prior_theta.py). Nothing else in the card moves.
#
#  2. prior_sigmas=lambda2_nu=nan,lambda4_nu=nan. The model puts a sigma=1 THETA
#     prior on every reparametrised lambda by default -- physically
#     lambda2_nu = 0.15 +- 0.10 and lambda4_nu = 0 +- 0.50 (the card's own
#     widths). Leaving those on while adding the lattice term would DOUBLE
#     COUNT the CS sector. nan frees them (fitter.py: mask = isfinite & > 0), so
#     the lattice term is the sole constraint on the CS kernel. The TMD lambdas
#     (lambda2, lambda4, delta_lambda2) KEEP their sigma=1 priors -- the lattice
#     says nothing about the TMD boundary condition, and AN-25-085 is explicit
#     that it has no robust external constraint.
#
# NO WALL. The point of the arm is whether an external-data PRIOR keeps the NP
# physical on its own, with uncertainties that stay data-determined -- unlike
# the wall, where lambda2_nu rails at the margin.
#
# --doImpacts deliberately dropped (as in the walled arm): nothing compared here
# uses it, and it costs ~30 min.
#
# --snapshotFile IS NOT OPTIONAL: rabbit's SIGTERM handler is a no-op without a
# filename, so a fit launched without it cannot be stopped without losing
# everything.
#
# BLINDING: alpha_s is blinded additively; no central value is printed here or
# in the log. sigma, losses, EDM and p-values are safe.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-lattice-constraints
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260911-lattice/card_latticeCS.hdf5
OUT=$CEPH/260911_lattice
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
PS="prior_sigmas=lambda2_nu=nan,lambda4_nu=nan"
mkdir -p $OUT
TS=$(date +%y%m%d_%H%M%S)
POSTFIX=${1:-DATALAT}
$T/scripts/run.sh $T/logs/fit_${POSTFIX}_$TS.log \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --snapshotInterval 0.25 --postfix $POSTFIX -t 0 --earlyStopping 100 \
    --snapshotFile $OUT/snapshot_$POSTFIX.hdf5 \
    --saveHists --computeHistErrors \
    --paramModel $MODEL $M "$PS"
echo "LAUNCH_DONE $POSTFIX"
