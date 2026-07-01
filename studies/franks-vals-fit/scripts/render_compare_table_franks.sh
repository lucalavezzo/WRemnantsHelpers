#!/bin/bash
# Render the FranksVals postfit-NP comparison table. Missing fitresults
# files (e.g. inflate5x still queued) are skipped gracefully with a WARN.
set -e

B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
PS=ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile

OUT="${MY_PLOT_DIR}/260519_franks_vals_compare"
SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/build_compare_table_franks.py"

SPECS=(
    "nominal=$B/260519_franks_vals_quad_realdata/${PS}_franks_vals_quad_realdata/fitresults.hdf5"
    "nominal_fakelumi=$B/260519_franks_vals_quad_fakelumi_realdata/${PS}_franks_vals_quad_fakelumi_realdata/fitresults.hdf5"
    "asym=$B/260519_franks_vals_asym_realdata/${PS}_franks_vals_asym_realdata/fitresults.hdf5"
    "asym_fakelumi=$B/260519_franks_vals_asym_fakelumi_realdata/${PS}_franks_vals_asym_fakelumi_realdata/fitresults.hdf5"
    "inflate5x=$B/260519_franks_vals_quad_inflate5x_realdata/${PS}_franks_vals_quad_inflate5x_realdata/fitresults.hdf5"
    "inflate5x_fakelumi=$B/260519_franks_vals_quad_inflate5x_fakelumi_realdata/${PS}_franks_vals_quad_inflate5x_fakelumi_realdata/fitresults.hdf5"
    "asym_inflate5x=$B/260519_franks_vals_asym_inflate5x_realdata/${PS}_franks_vals_asym_inflate5x_realdata/fitresults.hdf5"
    "asym_inflate5x_fakelumi=$B/260519_franks_vals_asym_inflate5x_fakelumi_realdata/${PS}_franks_vals_asym_inflate5x_fakelumi_realdata/fitresults.hdf5"
    "asym_reg=$B/260519_franks_vals_asym_reg_realdata/${PS}_franks_vals_asym_reg_realdata/fitresults.hdf5"
    "asym_reg_fakelumi=$B/260519_franks_vals_asym_reg_fakelumi_realdata/${PS}_franks_vals_asym_reg_fakelumi_realdata/fitresults.hdf5"
    "quadratic=$B/260520_franks_vals_quadratic_realdata/${PS}_franks_vals_quadratic_realdata/fitresults.hdf5"
    "quadratic_fakelumi=$B/260520_franks_vals_quadratic_fakelumi_realdata/${PS}_franks_vals_quadratic_fakelumi_realdata/fitresults.hdf5"
    "lambda4asym=$B/260520_franks_vals_lambda4asym_realdata/${PS}_franks_vals_lambda4asym_realdata/fitresults.hdf5"
    "lambda4asym_fakelumi=$B/260520_franks_vals_lambda4asym_fakelumi_realdata/${PS}_franks_vals_lambda4asym_fakelumi_realdata/fitresults.hdf5"
)

python "$SCRIPT" "${SPECS[@]}" --mode physical -o "$OUT"
python "$SCRIPT" "${SPECS[@]}" --mode theta    -o "$OUT"

# pdflatex isn't in the container; compile on the host if we're outside it.
if command -v pdflatex >/dev/null 2>&1; then
    for f in "$OUT/np_compare_franks.tex" "$OUT/np_compare_franks_theta.tex"; do
        [ -f "$f" ] && ( cd "$OUT" && pdflatex -interaction=batchmode "$(basename "$f")" > /dev/null )
    done
fi
echo "Wrote $OUT/np_compare_franks{,_theta}.{tex,pdf}"
