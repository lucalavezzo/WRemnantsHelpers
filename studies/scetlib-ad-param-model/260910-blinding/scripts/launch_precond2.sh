#!/bin/bash
# PRECONDITIONED blinded data fit, take 2 -- with the preconditioner actually
# SCOPED to the block that misbehaves.
#
# Take 1 was a NO-OP and the log said so plainly:
#   "No --preconditionParams given; selecting all 1 unconstrained parameters"
#   "Auto-blocking 1 parameters ... 1 block(s), largest 1"
#   "condition number 1 -> 1  [alphaS]"
# By default the preconditioner takes only UNCONSTRAINED parameters, on the
# stated rationale that "constrained nuisances are already normalised by their
# prior". Our fit violates exactly that: the NP lambdas and profile scales carry
# sigma = 1 priors in theta, so they LOOK normalised, but the DATABLIND postfit
# has lambda4 at sigma 0.0115 and resumScaleMuF at 0.0547 against priors of 1 --
# pinned 20-90x tighter than the prior. The Hessian in that block is therefore
# wildly non-unit, and the default heuristic excludes precisely it. alphaS is
# the only unconstrained parameter, and a 1x1 block has condition number 1 by
# construction, hence the no-op.
#
# So name the model's own 47 parameters as the scope. Card nuisances are left
# out: there are 3673 of them, all well behaved (max |pull| 1.22, ZERO beyond
# 2 sigma in DATABLIND), and including them would be enormously expensive.
#
# --preconditionBlocks none factorises the whole scope as ONE block, keeping the
# NP <-> scale cross-correlations, which is where the pathology lives. It "fails
# entirely if any part of the scope is singular" -- acceptable here because the
# known-inert direction (resumTNP_b_qqDS, identically zero gradient for the Z)
# is in params.DEFAULT_FROZEN and frozen parameters are always excluded.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_blinding_final
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
exec $T/scripts/run.sh $T/logs/fit_DATAPC2_$(date +%y%m%d_%H%M%S).log \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix DATAPC2 -t 0 --earlyStopping 100 --stallRelTol 1e-5 \
    --precondition --preconditionBlocks none \
    --preconditionParams 'alphaS' 'lambda.*' 'delta_lambda2' 'b0_over_bmax_nu' \
                         'resumTNP_.*' 'resumScale.*' 'resumTransition.*' 'pdfEig.*' \
    --snapshotFile $OUT/snapshot_DATAPC2.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors --doImpacts \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
