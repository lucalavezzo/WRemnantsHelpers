#!/bin/bash
# STEP 5 of REPRODUCE.md: the nominal alpha_s fit, exactly as NOMSTIFF ran it
# (fitresults_NOMSTIFF.hdf5 meta_info["command"]), with the paths made variables.
#
#   usage: step5_fit.sh <outdir> <postfix> <seed fitresult> [extra rabbit_fit.py args...]
#   env:   CACHE  cache directory holding cache.npz + cache.conf
#                 (default: the /scratch mirror NOMSTIFF read; the ceph master is md5-identical)
#          CARD   datacard (default: card A + ASWZ lattice term, lambda4_nu = 0 slice)
#          STEP5_PYTHON  interpreter (default python3; check_step5_argv.py swaps in an argv dumper)
#
# Must run inside the WMass container with SCETLIB_BUILD pointing at a SCETlib build that reads
# rules v13 / fo v14 (NOMSTIFF: WRemnants/scetlib-cms @ 2dd978a). From WRemnantsHelpers:
#   ./agent_setup.sh --scetlib current -- scripts/.../step5_fit.sh <outdir> <postfix> <seed>
#
# NOMSTIFF itself ran WITHOUT the postfit products (saturated tests, impacts, hists). For the full
# product add (as workflows/fitterAD.sh does):
#   -m Project ch0 ptll --computeSaturatedProjectionTests --computeHistErrors \
#   --doImpacts --globalImpacts --globalImpactsDisableJVP --saveHists
set -u
OUT=${1:?outdir}; PF=${2:?postfix}; SEED=${3:?seed fitresult}; shift 3
CARD=${CARD:-/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260923_lattice_fits/cards/cardA_latticeASWZ_l4zero_statsyst.hdf5}
CACHE=${CACHE:-/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero}
: "${SCETLIB_BUILD:?SCETLIB_BUILD is not set: source the scetlib-cms setup.sh (or use agent_setup.sh)}"
# 44 of the cache's 53 SCETlib parameters: the model default fitted set minus lambda4_nu (held at
# its anchor 0, so it never reaches rabbit). Order as in NOMSTIFF.
FIT_PARAMS=alphaS,lambda2,lambda4,delta_lambda2,lambda2_nu
FIT_PARAMS+=,resumTNP_gamma_cusp,resumTNP_gamma_mu_q,resumTNP_gamma_nu,resumTNP_s
FIT_PARAMS+=,resumTNP_b_qqV,resumTNP_b_qqbarV,resumTNP_b_qqS,resumTNP_b_qg,resumTNP_h_qqV
FIT_PARAMS+=,resumTransition2
for i in $(seq 0 28); do FIT_PARAMS+=,pdfEig$i; done
WALL=wremnants.postprocessing.scetlib_ad.np_damping_wall
mkdir -p "$OUT"
exec ${STEP5_PYTHON:-python3} "$WREM_BASE/rabbit/bin/rabbit_fit.py" "$CARD" --jitCompile off -o "$OUT" -t 0 --postfix "$PF" \
  --regularizationStrength 8 -r $WALL.NPDampingWall $WALL.NPDampingMapping margin=0 \
  --snapshotFile "$OUT/snapshot_fitresults_$PF.hdf5" --snapshotInterval 0.25 \
  --paramModel wremnants.postprocessing.scetlib_ad.SCETlibADParamModel \
    cache="$CACHE/cache.npz" conf="$CACHE/cache.conf" threads=128 \
    fit_params="$FIT_PARAMS" prior_sigmas=lambda2_nu=nan \
  -v 4 --earlyStopping 100 --externalPostfit "$SEED" "$@"
