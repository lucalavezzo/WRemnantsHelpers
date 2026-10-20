#!/usr/bin/env bash
# P2: the nominal card's exact setupRabbit command (meta_info of 260916_Z_2D_card_adcorr/.../ZMassDilepton.hdf5, WRemnants c838fc63)
# re-run with the current tree, + prior inflation. C0 = control (no change), to check the current tree reproduces the card.
# usage: agent_setup.sh -- bash build_cards_p2.sh <variant> [<variant> ...]
set -f
OUTB=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261018_ptll_gof_tests/cards
IN=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260915_Z_histmaker_adcorr/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV_Corr_maxFiles_m1_adcorr.hdf5
cd $WREM_BASE
echo "[cards] WRemnants $(git rev-parse --short HEAD); dirty: $(git status --short | wc -l) entries"
for V in "$@"; do
  case $V in
    C0)   EXTRA=() ;;
    A0x2) EXTRA=(--scaleParams 'helicity_0=2') ;;
    A0x3) EXTRA=(--scaleParams 'helicity_0=3') ;;
    THx2) EXTRA=(--scaleParams 'helicity_0=2' 'mb_|pdfMSHT20m[bc]range=2' '^weak_|sin2thetaZ|widthZ=2' 'horace=2' --lumiUncertainty 1.024144) ;;
    FREELUMI) EXTRA=(--lumiUncertainty 0) ;;  # P5a: --fakelumi was removed (WRemnants 0769d44b); lumi unconstrained instead
    *) echo "unknown variant $V"; continue ;;
  esac
  echo "[cards] $(date -Is) building $V: ${EXTRA[*]}"
  python scripts/rabbit/setupRabbit.py -i $IN --fitvar 'ptll-yll' -o $OUTB/ --noi alphaS --npUnc none --axlim ptll 0j 44j \
    --postfix adexclpdf_$V --realData \
    --excludeNuisances '^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|resumTransitionFOScale|scetlib_dyturbo.*pdfas.*|scetlib_dyturbo.*CT18Z.*pdfvars.*)' \
    --storeResponseMatrix --pseudoData nominal -v 3 --responseMatrixGenBinning response "${EXTRA[@]}"
  echo "[cards] $(date -Is) $V exit $?"
done
