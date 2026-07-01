#!/bin/bash
# 4D fit grid for 260430_debug study.
#
# For each configuration:
#   1. Run setupRabbit.py to produce ZMassDilepton.hdf5 (skipped if it exists).
#   2. Run rabbit_fit.py -t  0 → fitresults.hdf5         (real data; skipped if it exists).
#   3. Run rabbit_fit.py -t -1 → fitresults_asimov.hdf5 (asimov;     skipped if it exists).
#
# rabbit_fit's --outname puts the asimov result alongside the data result in
# the same dir, so we don't duplicate ZMassDilepton.hdf5 (~1GB each).
#
# Idempotent: re-running the script picks up where it left off.

set +e   # never abort on per-fit failure
source /opt/venv/bin/activate
cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
source setup.sh > /dev/null 2>&1 || true

OUT="${MY_OUT_DIR}/260430_debug"
HISTIN="/scratch/submit/cms/areimers/alphas/histmaker/AlphaS/Unblinding/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4BugfixLambda6_CT18Z_N3p0LL_N2LO_Corr_maxFiles_m1.hdf5"
SETUP="${WREM_BASE}/scripts/rabbit/setupRabbit.py"
FIT="${WREM_BASE}/rabbit/bin/rabbit_fit.py"

mkdir -p "$OUT"

# 4D fitvar: setupRabbit treats each --fitvar entry as one channel's axes,
# split by '-'. Pass a single dash-separated string to get a 4-axis channel
# (this matches the existing dir naming convention
# ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_<postfix>).
# Passing 4 separate args silently produces a 1D fit on `ptll` only.
COMMON_SETUP=(--fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile'
              --noi alphaS --axlim ptll 0j 44j --verbose 3
              -i "$HISTIN" --npUnc LatticeNoConstraints --pdfUncFromCorr
              -o "$OUT/" --realData)

# Real-data fit: post-processing.
# We attempt --computeSaturatedProjectionTests first; if that crashes
# (Cholesky failure on stressed configs corrupts fitresults.hdf5 to
# ~27 KB), the run_one_config wrapper deletes the truncated file and
# retries with COMMON_FIT_DATA (no sat tests).
COMMON_FIT_DATA=(--computeVariations -m Project ch0 ptll
                 --computeHistErrors --computeHistImpacts --doImpacts
                 --globalImpacts --saveHists --saveHistsPerProcess
                 -t 0)
COMMON_FIT_DATA_WITH_SAT=("${COMMON_FIT_DATA[@]}" --computeSaturatedProjectionTests)
# After the run, fitresults.hdf5 must be at least this many bytes for us
# to consider it a successful fit. Sub-MB files indicate the writer
# crashed mid-write (typical Cholesky-failure footprint is ~27 KB).
MIN_FITRESULTS_BYTES=1000000

# Asimov fit: minimal — we only need σ(α_s) and impacts for the column.
# Drop sat-p tests (asimov p=1 trivially) and hist saving (not used).
COMMON_FIT_ASIMOV=(--doImpacts --globalImpacts -t -1
                   --outname fitresults_asimov.hdf5)

# ----------------------------------------------------------------------
# Configurations.
#
# Each row: postfix | extra setupRabbit args
# Postfix is appended to "ZMassDilepton_<fitvars>_". "LatticeNoConstraints"
# prefix on every postfix matches the existing dir naming convention.
# ----------------------------------------------------------------------
declare -a CONFIGS=(
    # --- existing 4D fits (already have data result; only asimov needed) ---
    "LatticeNoConstraints"
    "LatticeNoConstraints_fakelumi|--fakelumi 1.1"
    "LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0|--scaleParams chargeVgenNP0scetlibNPZlambda4=5"
    "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0|--scaleParams chargeVgenNP0scetlibNP=5.0"
    "LatticeNoConstraints_chargeVgenNP0scetlibNPScale5p0_fakelumi|--scaleParams chargeVgenNP0scetlibNP=5.0 --fakelumi 1.1"
    "LatticeNoConstraints_ScetlibNoSymmetrize|--noSymmetrize scetlib"
    "LatticeNoConstraints_scetlibScale5p0|--scaleParams scetlib=5.0"
    "LatticeNoConstraints_scetlibNoConstraint|--noConstrainParams scetlibNP"
    # --- new 4D fits (need setup + data + asimov) ---
    "LatticeNoConstraints_chargeVgenNP0scetlibNPZlambda4Scale5p0_fakelumi|--scaleParams chargeVgenNP0scetlibNPZlambda4=5 --fakelumi 1.1"
    "LatticeNoConstraints_ScetlibNoSymmetrize_fakelumi|--noSymmetrize scetlib --fakelumi 1.1"
    "LatticeNoConstraints_scetlibScale5p0_fakelumi|--scaleParams scetlib=5.0 --fakelumi 1.1"
    "LatticeNoConstraints_scetlibNoConstraint_fakelumi|--noConstrainParams scetlibNP --fakelumi 1.1"
    "LatticeNoConstraints_scetlibNoLambdaInfScale5p0|--scaleParams scetlib(?!.*LambdaInf)=5.0"
    "LatticeNoConstraints_scetlibNoLambdaInfScale5p0_fakelumi|--scaleParams scetlib(?!.*LambdaInf)=5.0 --fakelumi 1.1"
    "LatticeNoConstraints_scetlibNoLambdaInfNoConstraint|--noConstrainParams scetlibNP(?!.*LambdaInf)"
    "LatticeNoConstraints_scetlibNoLambdaInfNoConstraint_fakelumi|--noConstrainParams scetlibNP(?!.*LambdaInf) --fakelumi 1.1"
    "LatticeNoConstraints_scetlibScale2p0|--scaleParams scetlib=2.0"
    "LatticeNoConstraints_scetlibScale2p0_fakelumi|--scaleParams scetlib=2.0 --fakelumi 1.1"
    # γ_Λ∞ kept at lattice prior with σ×3, all other 5 SCETlib NPs
    # (incl. γ_Λ₂/Λ₄ rescaled back from ×10 to ×1) unconstrained,
    # plus fakelumi.
    "LatticeNoConstraints_LambdaInfTight3_fakelumi|--scaleParams scetlibNPgammaLambda2|scetlibNPgammaLambda4=0.1 scetlibNPgammaLambdaInf=0.3 --noConstrainParams scetlibNP(?!.*LambdaInf) --fakelumi 1.1"
    # All 3 γ NPs constrained at ×3 the lattice σ (down from ×10).
    # chargeV NPs (λ₂, Δλ₂, λ₄) unconstrained. + fakelumi.
    "LatticeNoConstraints_gammaTight3_fakelumi|--scaleParams scetlibNPgamma=0.3 --noConstrainParams chargeVgenNP0scetlibNP --fakelumi 1.1"
    # All 6 SCETlib NPs constrained at ×3 their lattice / cookbook σ
    # (γ NPs ×0.3 of the LatticeNoConstraints ×10 baseline = ×3;
    # chargeV NPs ×3 of their default kfactor=1). +/- fakelumi.
    "LatticeNoConstraints_allNPConstr3|--scaleParams scetlibNPgamma=0.3 chargeVgenNP0scetlibNP=3.0"
    "LatticeNoConstraints_allNPConstr3_fakelumi|--scaleParams scetlibNPgamma=0.3 chargeVgenNP0scetlibNP=3.0 --fakelumi 1.1"
)

# ----------------------------------------------------------------------
run_one_config () {
    local row="$1"
    local postfix="${row%%|*}"
    local extra="${row#*|}"
    [ "$extra" = "$row" ] && extra=""   # no '|' means no extra args

    # eval is needed so the regex in --scaleParams 'scetlib(?!.*LambdaInf)=5.0'
    # is parsed as a single argument by setupRabbit. We pass the unsplit
    # string to setupRabbit via xargs-style array expansion.
    read -ra extra_arr <<<"$extra"

    local newdir="$OUT/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_${postfix}"
    mkdir -p "$newdir"

    echo ""
    echo "############################################################"
    echo "### $(date)  postfix=${postfix}"
    echo "### dir=${newdir}"
    [ -n "$extra" ] && echo "### extra=${extra}"
    echo "############################################################"

    # 1. setupRabbit (skip if input tensor already there)
    if [ -f "$newdir/ZMassDilepton.hdf5" ]; then
        echo "[skip setup] ZMassDilepton.hdf5 already exists"
    else
        echo "--- setupRabbit ---"
        python "$SETUP" "${COMMON_SETUP[@]}" -p "$postfix" "${extra_arr[@]}"
    fi

    # 2. real-data fit (with sat tests; fall back to no-sat-tests if the
    # saturated post-processing corrupts the output file)
    if [ -f "$newdir/fitresults.hdf5" ] && [ "$(stat -c %s "$newdir/fitresults.hdf5")" -ge "$MIN_FITRESULTS_BYTES" ]; then
        echo "[skip data fit] fitresults.hdf5 already exists ($(stat -c %s "$newdir/fitresults.hdf5") bytes)"
    else
        # Decide whether to bother attempting sat tests. If a truncated
        # fitresults.hdf5 already sits there (from a previous run that
        # crashed in the saturated-projection post-processing), skip
        # straight to no-sat-tests.
        had_truncated=0
        if [ -f "$newdir/fitresults.hdf5" ]; then
            sz=$(stat -c %s "$newdir/fitresults.hdf5")
            echo "[purge stale] fitresults.hdf5 is ${sz} bytes (< ${MIN_FITRESULTS_BYTES}), deleting"
            rm "$newdir/fitresults.hdf5"
            had_truncated=1
        fi

        if [ "$had_truncated" -eq 0 ]; then
            echo "--- rabbit_fit (data, -t 0, with sat tests) ---"
            python "$FIT" "$newdir/ZMassDilepton.hdf5" \
                "${COMMON_FIT_DATA_WITH_SAT[@]}" -o "$newdir/"
            sz=$(stat -c %s "$newdir/fitresults.hdf5" 2>/dev/null || echo 0)
        else
            sz=0
        fi

        if [ "$sz" -lt "$MIN_FITRESULTS_BYTES" ]; then
            if [ "$had_truncated" -eq 1 ]; then
                echo "[fallback known] previous run left a truncated fitresults.hdf5 (sat-tests crashed before); going straight to no-sat-tests"
            else
                echo "[fallback] fitresults.hdf5 truncated to $sz bytes (sat-tests Cholesky probably failed); retrying without --computeSaturatedProjectionTests"
            fi
            # Persistent marker so build_tables.py can distinguish
            # "Cholesky failed" (sat-p un-computable) from "sat tests
            # never attempted" — both produce a fitresults.hdf5 with no
            # saturated chi2 in mappings.
            touch "$newdir/cholesky_failed.flag"
            rm -f "$newdir/fitresults.hdf5"
            python "$FIT" "$newdir/ZMassDilepton.hdf5" \
                "${COMMON_FIT_DATA[@]}" -o "$newdir/"
        fi
    fi

    # 3. asimov fit
    if [ -f "$newdir/fitresults_asimov.hdf5" ]; then
        echo "[skip asimov] fitresults_asimov.hdf5 already exists"
    else
        echo "--- rabbit_fit (asimov, -t -1) ---"
        python "$FIT" "$newdir/ZMassDilepton.hdf5" \
            "${COMMON_FIT_ASIMOV[@]}" -o "$newdir/"
    fi

    echo "--- DONE $(date) postfix=${postfix} ---"
}

# Optional first-arg filter: pass a regex to run only matching postfixes.
# Useful for smoke tests, e.g.
#     run_4d_grid.sh '^LatticeNoConstraints_scetlibScale2p0$'
FILTER="${1:-}"

echo "BEGIN $(date)  output: $OUT"
for row in "${CONFIGS[@]}"; do
    postfix="${row%%|*}"
    if [ -n "$FILTER" ] && ! [[ "$postfix" =~ $FILTER ]]; then
        continue
    fi
    run_one_config "$row"
done
echo ""
echo "ALL_DONE $(date)"
