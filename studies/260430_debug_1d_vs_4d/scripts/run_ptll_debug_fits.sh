#!/bin/bash
# Re-run each fit in $MY_OUT_DIR/260430_debug/ with --fitvar 'ptll'.
# For *fakelumi* variants, append --fakelumi 1.1 to setupRabbit.

set +e   # do not abort on per-fit failure — log and continue with the next fit
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

OUT="${MY_OUT_DIR}/260430_debug"
HISTIN="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
SETUP="${WREM_BASE}/scripts/rabbit/setupRabbit.py"
FIT="${WREM_BASE}/rabbit/bin/rabbit_fit.py"

# Common setupRabbit args
COMMON_SETUP=(--fitvar 'ptll' --noi alphaS --axlim ptll 0j 44j --verbose 3
              -i "$HISTIN" --npUnc LatticeNoConstraints --pdfUncFromCorr
              -o "$OUT/" --realData)

# Common rabbit_fit args (default for all but _noAlphaS)
COMMON_FIT_FULL=(--computeVariations -m Project ch0 ptll
                 --computeHistErrors --computeHistImpacts --doImpacts
                 --globalImpacts --saveHists --saveHistsPerProcess
                 -t 0)

# Reduced flag set for the noAlphaS variant (matches the original)
COMMON_FIT_NOALPHAS=(-m Project ch0 ptll --doImpacts
                     --globalImpacts -t 0)

run_fit () {
    local postfix="$1"
    shift
    local extra_setup=("$@")  # remaining args = extra setupRabbit args
    local newdir="$OUT/ZMassDilepton_ptll_${postfix}"

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

# 9 fits, in same order as the existing dirs
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
