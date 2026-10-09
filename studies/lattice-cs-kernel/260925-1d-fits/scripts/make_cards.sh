#!/usr/bin/env bash
# 1D cards (ptll only / yll only) built with card A's OWN code: WRemnants c838fc6 + the git_diff recorded in card A's
# meta_info (WRemnants files only), checked out as the worktree below. Current main cannot rebuild card A: ede643dc
# replaced the (never-committed) sidecar-name resolver card A was built with, and the pdfas lookup then fails.
# Submodules (narf/rabbit/wums/wremnants-data) are symlinked from the main tree (rabbit = 2a59246, card A had f77f10e).
# Differences to card A's command: --fitvar, -o, and for yll '--presel ptll:sum 0j 44j' instead of '--axlim ptll 0j 44j'
# (axlim only accepts fit variables; presel ptll:sum restricts ptll to [0,44] and then sums it away).
set -uo pipefail
VAR=$1   # ptll | yll
A=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS
WT=/work/submit/lavezzo/alphaS/wrem-cardA-c838fc6
if [ "$VAR" = yll ]; then LIM=(--presel ptll:sum 0j 44j); else LIM=(--axlim ptll 0j 44j); fi
cd $WT
export PYTHONPATH=$WT:${PYTHONPATH:-}
python scripts/rabbit/setupRabbit.py -i "$A/260915_Z_histmaker_adcorr/mz_dilepton_scetlib_dyturbo_LatticeNPLambda4Bugfix_FranksValsVars_CT18Z_N3p0LL_N2LO_adcorrAV_Corr_maxFiles_m1_adcorr.hdf5" \
  --fitvar "$VAR" -o "$A/260925_Z_1D_card_adcorr/" --noi alphaS --npUnc none "${LIM[@]}" --postfix adexclpdf --realData \
  --excludeNuisances '^(resumTNP|scetlibNP|resumScaleZ|resumFOScaleZ|resumTransitionFOScale|scetlib_dyturbo.*pdfas.*|scetlib_dyturbo.*CT18Z.*pdfvars.*)' \
  --storeResponseMatrix --pseudoData nominal -v 3 --responseMatrixGenBinning response
