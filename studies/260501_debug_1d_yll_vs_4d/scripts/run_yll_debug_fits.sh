#!/bin/bash
# Re-run each fit in $MY_OUT_DIR/260430_debug/ with --fitvar 'yll' (1D yll).
# Same 9 configs and same setupRabbit / rabbit_fit invocation as the ptll
# study (260430_debug_1d_vs_4d/), with ptll -> yll substitutions.
#
# NOTE: --axlim ptll 0j 44j is intentionally kept — that slices the input
# histogram on ptll before integrating ptll out, so the 1D-yll data is on
# the same ptll-restricted slice as the 4D and 1D-ptll fits.
#
# NOTE: the _scetlibNoConstraint config requires a manual source patch in
# wremnants/postprocessing/rabbit_theory_helper.py (uncomment the three
# `noConstraint=True` lines around 751/880/979). This wrapper will produce
# a *constrained* fit for that postfix; redo it after applying the patch
# (per 260430_debug_1d_vs_4d/runlog.md).

set +e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

OUT="${MY_OUT_DIR}/260430_debug"
HISTIN="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
SETUP="${WREM_BASE}/scripts/rabbit/setupRabbit.py"
FIT="${WREM_BASE}/rabbit/bin/rabbit_fit.py"

COMMON_SETUP=(--fitvar 'yll' --noi alphaS --presel ptll 0j 44j --verbose 3
              -i "$HISTIN" --npUnc LatticeNoConstraints --pdfUncFromCorr
              -o "$OUT/" --realData)

COMMON_FIT_FULL=(--computeVariations -m Project ch0 yll
                 --computeHistErrors --computeHistImpacts --doImpacts
                 --globalImpacts --saveHists --saveHistsPerProcess
                 -t 0)

COMMON_FIT_NOALPHAS=(-m Project ch0 yll --doImpacts
                     --globalImpacts -t 0)

run_fit () {
    local postfix="$1"
    shift
    local extra_setup=("$@")
    local newdir="$OUT/ZMassDilepton_yll_${postfix}"

    echo ""
    echo "###########################################################"
    echo "### $(date)  postfix=${postfix}"
    echo "### outdir=${newdir}"
    echo "###########################################################"

    echo "--- setupRabbit ---"
    python "$SETUP" "${COMMON_SETUP[@]}" -p "$postfix" "${extra_setup[@]}"

    echo "--- rabbit_fit ---"
    if [[ "$postfix" == *"noAlphaS"* ]]; then
        python "$FIT" "$newdir/ZMassDilepton.hdf5" \
            "${COMMON_FIT_NOALPHAS[@]}" -o "$newdir/"
    else
        python "$FIT" "$newdir/ZMassDilepton.hdf5" \
            "${COMMON_FIT_FULL[@]}" -o "$newdir/"
    fi
    echo "--- DONE $(date) postfix=${postfix} ---"
}

run_fit "LatticeNoConstraints"

run_fit "LatticeNoConstraints_ScetlibNoSymmetrize" --noSymmetrize scetlib

run_fit "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0" \
    --scaleParams 'chargeVgenNP0scetlibNP=5.0'

run_fit "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0_fakelumi" \
    --scaleParams 'chargeVgenNP0scetlibNP=5.0' --fakelumi 1.1

run_fit "LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0" \
    --scaleParams 'chargeVgenNP0scetlibNPZlambda4=5'

run_fit "LatticeNoConstraints_fakelumi" --fakelumi 1.1

run_fit "LatticeNoConstraints_fakelumi_noAlphaS" --fakelumi 1.1 \
    --excludeNuisances 'scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_pdfas_CorrByHelicity'

run_fit "LatticeNoConstraints_scetlibNoConstraint"

run_fit "LatticeNoConstraints_scetlibScale5p0" --scaleParams 'scetlib=5.0'

echo ""
echo "ALL_DONE_OK $(date)"
