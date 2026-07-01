#!/bin/bash
# AN/LatticeNoConstraints histmaker, quadratic-symmetrized NPs
# (via setupRabbit_quadTest.py monkey-patch).  Run rabbit_fit
# --prefitOnly so we only need the prefit tensor + templates, no
# minimization.  Then plot Lambda_4 SymAvg + SymDiff prefit overlaid
# on ptll.
set -e
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

HM=/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5
QUAD_SETUP=$MY_WORK_DIR/studies/franks-vals-fit/scripts/setupRabbit_quadTest.py

POSTFIX=AN_quadratic_prefitOnly
OUTDIR=$MY_OUT_DIR/260520_${POSTFIX}
PLOTDIR=$MY_PLOT_DIR/260520_${POSTFIX}
FITDIR=$OUTDIR/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${POSTFIX}
SETUP=$FITDIR/ZMassDilepton.hdf5

mkdir -p "$OUTDIR" "$PLOTDIR"

echo "=== setupRabbit_quadTest (AN histmaker, quadratic NPs) ==="
if [ ! -f "$SETUP" ]; then
    python "$QUAD_SETUP" \
        -i "$HM" \
        --fitvar ptll-yll-cosThetaStarll_quantile-phiStarll_quantile \
        -o "$OUTDIR" \
        --noi alphaS --pdfUncFromCorr \
        --npUnc LatticeNoConstraints \
        --axlim ptll 0j 44j \
        --postfix "$POSTFIX" \
        --realData
fi

echo "=== rabbit_fit --prefitOnly ==="
rabbit_fit.py "$SETUP" \
    -t 0 \
    -m Project ch0 ptll \
    --prefitOnly \
    --computeVariations \
    --computeHistErrors \
    --saveHists \
    -o "$FITDIR"

FIT=$FITDIR/fitresults.hdf5

echo "=== Plot Lambda_4 SymAvg + SymDiff prefit on ptll ==="
rabbit_plot_hists.py "$FIT" \
    --prefit \
    -m 'Project ch0 ptll' \
    --varNames chargeVgenNP0scetlibNPZlambda4SymAvg chargeVgenNP0scetlibNPZlambda4SymDiff \
    --varLabels 'AN $\Lambda_4$ SymAvg' 'AN $\Lambda_4$ SymDiff' \
    --config "$WREM_BASE/wremnants/utilities/styles/styles.py" \
    --title CMS --titlePos 0 --subtitle Preliminary \
    --processGrouping z_dilepton \
    --rrange 0.97 1.03 \
    --yscale 1.25 \
    --postfix AN_quad_Lambda4 \
    -o "$PLOTDIR"

echo "DONE_OK $(date)"
