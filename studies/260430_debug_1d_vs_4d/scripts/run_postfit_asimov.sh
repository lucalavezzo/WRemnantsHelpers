#!/bin/bash
# Run a "post-fit Asimov" rabbit_fit for each 4D config: same Asimov toy
# as the existing fitresults_asimov.hdf5, but with the toy generated from
# the data-postfit prediction (NPs at the data fit's pulled values)
# instead of the prefit nominal-MC prediction.
#
# Requires the local patch in rabbit_fit.py that loads --externalPostfit
# BEFORE computing the asimov yield (otherwise defaultassign() in the
# per-iteration loop wipes the externalPostfit values before the yield
# is computed).
#
# Output: fitresults_postfitAsimov.hdf5 alongside each fit dir's existing
# files. Idempotent (skips if the output already exists).
#
# Expectation: σ(α_s) from this fit should equal the data σ to numerical
# precision, since the fit's minimum is at the same point as the data
# fit (data = expected_yield_at_postfit by construction → set_nobs makes
# the data trivial to refit at the postfit values).

set +e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

OUT="${MY_OUT_DIR}/260430_debug"
FIT="${WREM_BASE}/rabbit/bin/rabbit_fit.py"

# Same 18 configs as run_4d_grid.sh (postfix names only).
declare -a POSTFIXES=(
    LatticeNoConstraints
    LatticeNoConstraints_fakelumi
    LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0
    LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0_fakelumi
    LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0
    LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0_fakelumi
    LatticeNoConstraints_ScetlibNoSymmetrize
    LatticeNoConstraints_ScetlibNoSymmetrize_fakelumi
    LatticeNoConstraints_scetlibScale5p0
    LatticeNoConstraints_scetlibScale5p0_fakelumi
    LatticeNoConstraints_scetlibNoLambdaInfScale5p0
    LatticeNoConstraints_scetlibNoLambdaInfScale5p0_fakelumi
    LatticeNoConstraints_scetlibScale2p0
    LatticeNoConstraints_scetlibScale2p0_fakelumi
    LatticeNoConstraints_scetlibNoConstraint
    LatticeNoConstraints_scetlibNoConstraint_fakelumi
    LatticeNoConstraints_scetlibNoLambdaInfNoConstraint
    LatticeNoConstraints_scetlibNoLambdaInfNoConstraint_fakelumi
)

FILTER="${1:-}"

echo "BEGIN $(date)  output: $OUT"
for postfix in "${POSTFIXES[@]}"; do
    if [ -n "$FILTER" ] && ! [[ "$postfix" =~ $FILTER ]]; then
        continue
    fi
    newdir="$OUT/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}"

    echo ""
    echo "############################################################"
    echo "### $(date)  postfit-Asimov  postfix=${postfix}"
    echo "############################################################"

    if [ ! -f "$newdir/ZMassDilepton.hdf5" ] || [ ! -f "$newdir/fitresults.hdf5" ]; then
        echo "[skip - missing inputs] need both ZMassDilepton.hdf5 and fitresults.hdf5"
        continue
    fi
    if [ -f "$newdir/fitresults_postfitAsimov.hdf5" ]; then
        echo "[skip already done] fitresults_postfitAsimov.hdf5 exists"
        continue
    fi

    python "$FIT" "$newdir/ZMassDilepton.hdf5" \
        --externalPostfit "$newdir/fitresults.hdf5" \
        --doImpacts --globalImpacts -t -1 \
        --outname fitresults_postfitAsimov.hdf5 \
        -o "$newdir/" 2>&1 | tail -8
    echo "--- DONE $(date) postfix=${postfix} ---"
done
echo ""
echo "ALL_DONE $(date)"
