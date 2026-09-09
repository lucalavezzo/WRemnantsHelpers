#!/bin/bash
# FIT TO DATA with preconditioning (rabbit PR #150).
#
# WHY: the unpreconditioned fit stalled at iteration 518 with the loss
# bit-identical for the next 100 iterations, then died computing the EDM with
# "Hessian is not positive-definite", potrf info=27 -- fit index 27 is POU 26 =
# pdfEig8. A negative curvature direction at a flat point means the minimizer
# stopped short of a stationary point with its outer steps being rejected,
# which is verbatim what --precondition targets.
#
# preconditionParams: the DEFAULT is every UNCONSTRAINED parameter, which here
# is only alphaS -- the model applies Gaussian priors to the other 46, so they
# count as constrained and would be skipped. The block that actually fails is
# the 29 PDF eigenvectors, so the theory block is named explicitly.
# preconditionBlocks=auto then reads the clusters off the reference matrix's
# correlations rather than trusting that naming.
set -e
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CARD=$CEPH/260908_Z_2D_card_acceptfix/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
OUT=$CEPH/study_scratch/260909-data-fit
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
exec rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
  --postfix DATAPC -t 0 --earlyStopping 100 \
  --precondition --preconditionBlocks auto \
  --preconditionParams '^alphaS$' '^lambda.*' '^delta_lambda2$' '^resum.*' '^pdfEig.*' \
  --saveHists --computeHistErrors --doImpacts \
  --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
