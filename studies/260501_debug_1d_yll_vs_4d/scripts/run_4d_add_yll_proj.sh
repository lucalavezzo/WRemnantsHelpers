#!/bin/bash
# Re-run each existing 4D fit with -m Project ch0 ptll AND -m Project ch0 yll
# so the saturated p-value on the yll projection is computed (the original
# 4D fits only included the ptll projection). Reuses the existing
# ZMassDilepton.hdf5 from the original fit dir; rabbit_fit only is re-run.
# Output: fitresults_withYllProj.hdf5 (postfix avoids clobbering the
# original fitresults.hdf5).

set +e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

OUT="${MY_OUT_DIR}/260430_debug"
FIT="${WREM_BASE}/rabbit/bin/rabbit_fit.py"

run_4d_yll () {
    local postfix="$1"
    local newdir="$OUT/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}"
    local infile="$newdir/ZMassDilepton.hdf5"

    echo ""
    echo "###########################################################"
    echo "### $(date)  4D + yll proj: ${postfix}"
    echo "### outdir=${newdir}"
    echo "###########################################################"

    if [[ ! -f "$infile" ]]; then
        echo "MISSING input $infile, skipping"
        return
    fi

    if [[ "$postfix" == *"noAlphaS"* ]]; then
        # noAlphaS variant — same reduced flag set as the original
        python "$FIT" "$infile" \
            -m Project ch0 ptll -m Project ch0 yll \
            --doImpacts --globalImpacts -t 0 \
            --postfix withYllProj -o "$newdir/"
    else
        python "$FIT" "$infile" \
            --computeVariations \
            -m Project ch0 ptll -m Project ch0 yll \
            --computeHistErrors --computeHistImpacts --doImpacts \
            --globalImpacts --saveHists --saveHistsPerProcess \
            --computeSaturatedProjectionTests -t 0 \
            --postfix withYllProj -o "$newdir/"
    fi
    echo "--- DONE $(date) postfix=${postfix} ---"
}

for postfix in \
    LatticeNoConstraints \
    LatticeNoConstraints_ScetlibNoSymmetrize \
    LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0 \
    LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0_fakelumi \
    LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0 \
    LatticeNoConstraints_fakelumi \
    LatticeNoConstraints_fakelumi_noAlphaS \
    LatticeNoConstraints_scetlibNoConstraint \
    LatticeNoConstraints_scetlibScale5p0; do
  run_4d_yll "$postfix"
done

echo ""
echo "ALL_DONE_OK $(date)"
