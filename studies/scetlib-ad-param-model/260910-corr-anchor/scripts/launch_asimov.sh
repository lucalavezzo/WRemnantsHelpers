#!/bin/bash
# NOT RUN for the anchor change, deliberately (Luca, 2026-09-10: "why do we
# need to run the asimov").  It would have had nothing to add:
#   * the anchor rebuilt from the correction is BIT-IDENTICAL to the cache's
#     on all 53 registered parameters (max|diff| = 0) and sigma_gen at
#     theta = 0 is unchanged at 670.0283701, so every downstream number is
#     identical by construction;
#   * the normalisation is a LINEAR change of variables, so
#     H_theta = J^T H_p J with J = width and sigma_physical = width *
#     sigma_theta = sigma_p identically.  Its only free numbers are the
#     widths, and each equals the old PRIOR_SIGMAS value exactly, so the
#     physical prior is unchanged too.  (A typo'd width WOULD be a real bug:
#     it survives the theta = 0 round-trip guard and shifts the physical
#     prior.  That is what the width table rules out.)
#   * and an Asimov fit never runs the minimiser (ifit = -1), so it cannot
#     probe the one thing that IS unmeasured -- whether collapsing the
#     curvature spread helps convergence.  That needs a TOY or DATA arm.
#
# Kept as the ready recipe for that toy arm.  Copied from
# 260908-fit-770/launch.sh arm AS770 (Asimov, adexclpdf, PRODUCTION config,
# threads=48); add `-t 1 --earlyStopping 100` for the toy.
#
# COMPARABILITY CAVEATS, before any number is read off this:
#   * rabbit DIFFERS from the AS770 reference.  That was rabbit @ 5bc7aad
#     (branch local-wip-260818); the submodule now sits at 9315f24 on main-plus-ours
#     (PR #156), which changes the preconditioner and blinding paths.
#   * the card is a COPY of the AS770 card with the `meta` dataset re-dumped to
#     carry scetlib_corr_config.  Physics content byte-identical (shutil.copyfile).
#   * REPORTED UNITS DIFFER.  Every reparametrised parameter is now a unit
#     nuisance, so the postfit vector reads theta, not the physical value:
#     AS770 recorded alphaS = 0.118, lambda2 = 0.4, ...; this run records 0.0 for
#     each.  Physical alphaS = 0.118 + 0.002 * theta, and physical
#     sigma(alphaS) = 0.002 * sigma_theta.  Compare in PHYSICAL units.
#   * An Asimov fit never runs the minimiser (ifit = -1), so the central values
#     ARE the start values by construction.  The only thing that can move is the
#     postfit uncertainty -- which is exactly what makes this a sharp check.
#
# DO NOT read alpha_s off this run: an Asimov fit is not blinded (rabbit sets
# blinded_fits = [f == 0 or (f > 0 and toysDataMode == "observed")]), and it is
# the model's own input anyway.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-corr-anchor
CEPH=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
CACHE=$CEPH/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$CEPH/study_scratch/260910-anchor-verify/card_none.hdf5
OUT=$CEPH/260910_anchor_asimov
MODEL=wremnants.postprocessing.scetlib_ad.SCETlibADParamModel
M="cache=$CACHE/cache.npz conf=$CACHE/cache.conf threads=48"
mkdir -p $OUT
exec $T/scripts/run.sh $T/logs/run_ASANCHOR_$(date +%y%m%d_%H%M%S).log \
  rabbit_fit.py $CARD -v 4 --jitCompile off --noBinByBinStat -o $OUT \
  --postfix ASANCHOR --paramModel $MODEL $M
