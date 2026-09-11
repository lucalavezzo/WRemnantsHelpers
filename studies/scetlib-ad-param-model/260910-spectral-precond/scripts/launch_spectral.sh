#!/bin/bash
# SPECTRAL-preconditioned blinded data fit.  Third arm of the preconditioning
# test, and byte-for-byte the DATAPC2 (ridge) command with ONE flag added:
#
#   --preconditionTransform spectral
#
# WHY.  DATAPC2 made things worse -- 411.08 at 292 iterations / 4049 s against
# the plain arm's 405.56 at 221 / 2645 s.  The reason is visible in its own
# preconditioner report:
#
#   all block has lam_min=-1.09e+03 (max|diag|=2.03e+04);
#     ridge from the spectrum: 0.0593 x max|diag|
#   ... condition number 4.22e+04 -> 1.75e+04, of which degeneracy 1.08e+05
#
# The reference Hessian is INDEFINITE at the start point (lam_min < 0), so the
# scalar ridge had to be raised to 5.9 % of max|diag| just to make the Cholesky
# succeed.  rabbit/preconditioner.py names that failure mode outright: one
# scalar ridge "swamps every direction softer than |lam_min| and leaves them
# near-null" -- i.e. it kills exactly the soft, degenerate directions (kappa_corr
# 1.08e+05) that preconditioning was supposed to fix.  Hence only 2.4x on kappa
# for 82.5 s of Hessian plus a worse minimum.
#
# 'spectral' factorises |H| = Q |Lambda| Q^T instead: every eigendirection gets
# its own scale, no scalar floor, and the SIGN of negative curvature is kept
# (trust-krylov uses negative curvature to escape saddles).  Its floor comes
# from the numerical rank, not from --preconditionRidge.
#
# The other options are deliberately left as DATAPC2 had them, which is also
# what preconditioner.py's CHOOSING THE OPTIONS recommends for spectral:
#   --preconditionBlocks none   under spectral a bigger block is always >= a
#                               split one (it whitens cross-terms exactly),
#                               so blocking is only a cost limit.  47 params.
#   --preconditionFrom hessian  (default) -- 'gaussnewton' exists only to
#                               guarantee the Cholesky and cannot represent
#                               negative curvature, so it is pointless here.
#   --preconditionRidge         untouched: ignored on this path.
#
# READING THE REPORT.  The after-side "degeneracy" is NOT reported (by design)
# and the after-side kappa on this path is partly an artefact: B and |B| share
# eigenvectors, so true kappa is identically 1 for any block where nothing was
# floored, while a correlation number picks up the arbitrary orientation of the
# Cholesky factor.  So judge this arm on the BEFORE-side kappa, n_floored, and
# the actual convergence -- not on the after-side number.
#
# --snapshotFile IS NOT OPTIONAL: rabbit's SIGTERM handler is a no-op without a
# filename (snapshot.py:161), so a fit launched without it cannot be stopped
# without losing everything.  Own snapshot file, own -o dir: DATAPC2 is still
# writing its postfit into 260910_blinding_final.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-spectral-precond
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_spectral
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
mkdir -p $OUT
LOG=$T/logs/fit_DATASPEC_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix DATASPEC -t 0 --earlyStopping 100 --stallRelTol 1e-5 \
    --precondition --preconditionBlocks none --preconditionTransform spectral \
    --preconditionParams 'alphaS' 'lambda.*' 'delta_lambda2' 'b0_over_bmax_nu' \
                         'resumTNP_.*' 'resumScale.*' 'resumTransition.*' 'pdfEig.*' \
    --snapshotFile $OUT/snapshot_DATASPEC.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors --doImpacts \
    --paramModel $MODEL cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128
