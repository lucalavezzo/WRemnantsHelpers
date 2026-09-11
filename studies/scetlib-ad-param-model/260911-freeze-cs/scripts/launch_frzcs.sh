#!/bin/bash
# knowledge/30_physics_global/np_parametrization_constraints.md §11 item 3 (and
# item 2): FREEZE the Collins-Soper lambda and refit.  Everything else exactly
# as ../260910-blinding/scripts/launch_final_test.sh ARM 1 ("plain DATABLIND").
#
# WHAT IS FROZEN, and why these two names.  The CS (gamma_nu^NP) sector of the
# SCETlib tanh form is lambda_inf_nu, lambda2_nu, lambda4_nu, b0_over_bmax_nu
# (lambda6_nu does not exist on this cache -- the runcard's CS form is tanh_2,
# verified in logs/probe_*.log: the 53 registered names carry no lambda6_nu).
# Of those, lambda_inf_nu AND b0_over_bmax_nu are ALREADY held by
# params.DEFAULT_FROZEN, so the CS sector's entire floating content on this card
# is lambda2_nu and lambda4_nu.  Freezing those two freezes the CS kernel.
#
# --freezeParameters, NOT the model's fit_params, and the reason is that this
# has to be a ONE-VARIABLE change against the plain arm:
#   * --freezeParameters keeps the registered parameter vector identical (47
#     params, same POI/POU split, same order, same priors, same impact groups,
#     same SCETlib rule set).  The ONLY difference from DATABLIND is two
#     tf.stop_gradient's (fitter.py get_model_nui).  So the postfit vector is
#     index-aligned with the five arms in ../260910-basins/basins.json and the
#     basin L2 needs no padding.
#   * fit_params=<45 names> would drop them from rabbit's vector entirely:
#     npou 46 -> 44, a different Hessian dimension, different impact groups, and
#     a postfit vector that no longer lines up with the existing arms.  Same
#     physics (the held value is the same anchor), more moving parts.
#   * rabbit handles frozen params correctly downstream: edmval_cov() inverts
#     only the floating submatrix and _resolved_param_impact_groups() drops
#     frozen indices.
# CAVEAT that comes with the choice: self.cov is initialised to
# diag(var_prefit) and only the FLOATING block is overwritten, so the frozen
# parameters' reported sigma in the fitresult is their PREFIT width (1.0 in
# theta), not a measurement.  Never quote it.
#
# WHERE they are frozen: at x0default = xparamdefault = theta 0, which the
# REPARAM 'unit' map sends to the CACHE ANCHOR -- i.e. the theory correction's
# own values, lambda2_nu = 0.15 GeV^2 and lambda4_nu = 0 GeV^4
# (logs/probe_*.log §3).  theta 0 is also the prior mean, so a frozen parameter
# contributes exactly zero prior penalty and the loss stays comparable.
#
# SCAN POINTS (§11 item 2).  xparam_default moves the START and, because the
# model declares no prior_means, the PRIOR MEAN with it (fitter.py:338-341), so
# each scan point is "best fit at lambda2_nu fixed, no prior on lambda2_nu" and
# the losses are directly comparable.  xparam_default is in THETA units for a
# reparametrised name; the map is physical = 0.15 + 0.10 * theta.
#
# usage: launch_frzcs.sh <anchor|lat0|lat087|lat05|lat19>
set -e
ARM=${1:-anchor}
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260911_freeze_cs
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=128"
mkdir -p $OUT

case $ARM in
  # THE HEADLINE ARM: frozen at the theory correction's own values, and the only
  # one with --doImpacts (it is the one whose NP-group impact is meaningful).
  anchor) POSTFIX=DATAFRZCS;  XPD="";                         IMPACTS="--doImpacts" ;;
  # scan: lambda2_nu = 0.00 (the damping-free edge of §10's 3 sigma lattice box)
  lat0)   POSTFIX=FRZCSL000;  XPD="xparam_default=lambda2_nu=-1.5"; IMPACTS="" ;;
  # scan: 0.05 GeV^2, the bottom of §11 item 4's expected [0.05, 0.15]
  lat05)  POSTFIX=FRZCSL050;  XPD="xparam_default=lambda2_nu=-1.0"; IMPACTS="" ;;
  # scan: 0.087 GeV^2, the lattice CENTRAL of §10 (Cridge-Marinelli-Tackmann)
  lat087) POSTFIX=FRZCSL087;  XPD="xparam_default=lambda2_nu=-0.63"; IMPACTS="" ;;
  # scan: 0.19 GeV^2, the TOP of §10's marginal 3 sigma box
  lat19)  POSTFIX=FRZCSL190;  XPD="xparam_default=lambda2_nu=0.4";  IMPACTS="" ;;
  *) echo "usage: launch_frzcs.sh <anchor|lat0|lat05|lat087|lat19>"; exit 2 ;;
esac

LOG=$T/logs/fit_${POSTFIX}_$(date +%y%m%d_%H%M%S).log
echo "$LOG" > $T/logs/LATEST_$POSTFIX
echo "[frzcs] arm=$ARM postfix=$POSTFIX xparam_default='$XPD'"
exec $T/scripts/run.sh $LOG \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
    --postfix $POSTFIX -t 0 --earlyStopping 100 \
    --freezeParameters lambda2_nu lambda4_nu \
    --snapshotFile $OUT/snapshot_$POSTFIX.hdf5 --snapshotInterval 0.25 \
    --saveHists --computeHistErrors $IMPACTS \
    --paramModel $MODEL $M $XPD
