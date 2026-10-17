#!/usr/bin/env bash
# PCLAT / PCNOLAT: the nominal cold main fit exactly as LAT / NOLAT (workflows/fitterAD.sh --constraints [--lattice],
# same card / cache / SCETlib build / -f), PLUS the full-scope spectral preconditioner, passed through -f because the
# shared fitterAD.sh could not be edited (its --constraints branch drops precond_arg). Runs INSIDE the container,
# with rabbit from the PINNED worktree (PR commit a606337). usage: pc_main_inner.sh <postfix> [--lattice]
RB=/work/submit/lavezzo/rabbit-tc-precond-val
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/261015_tc_precond_validation
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260916_Z_2D_card_adcorr/ZMassDilepton_ptll_yll_adexclpdf/ZMassDilepton.hdf5
CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921_y25
export PYTHONPATH=$RB:$PYTHONPATH
RF=$(python -c 'import rabbit, os; print(os.path.dirname(os.path.dirname(rabbit.__file__)))')
[ "$RF" = "$RB" ] || { echo "[pc_main] rabbit imports from $RF, not $RB: abort"; exit 1; }
echo "[pc_main] $(date +%FT%T) $1 rabbit=$(git -C $RB rev-parse --short HEAD) from $RF; fitterAD md5 $(md5sum /home/submit/lavezzo/alphaS/WRemnantsHelpers/workflows/fitterAD.sh | cut -c1-12)"
pf=$1; shift
set -f
exec bash /home/submit/lavezzo/alphaS/WRemnantsHelpers/workflows/fitterAD.sh "$CARD" -c "$CACHE" -o "$OUT" -p "$pf" --constraints "$@" \
  -f 'threads=128 -v 4 --precondition --preconditionParams .* --preconditionBlocks none --preconditionTransform spectral'
