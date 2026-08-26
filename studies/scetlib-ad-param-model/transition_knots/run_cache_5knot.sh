#!/bin/bash
# One arm of the muF knot-COUNT A/B: an 80-bin subset cache with the muF
# stencil set by MUF_NMEM (4 = five knots, 2 = three).
#
# Subset: ALL 10 |Y| bins x qT bins 13..20 =
#   [14,16] [16,18] [18,20] [20,24] [24,28] [28,33] [33,44] [44,100]
# All |Y| bins, so the |Y|-integrated response the closure plot shows is a
# COMPLETE sum in every qT bin it draws -- a ragged subset would fold to partial
# sums and read as disagreement. qT 13.. because the transition points are
# identically zero below qT 16 ([14,16] is kept as the null control) and because
# the lowest ptV bin costs more than all the others together.
set -e
NMEM="${1:-4}"; TAG="${2:-cache5}"; THREADS="${3:-64}"
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/fiveknot
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260820_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
export SINGULARITYENV_MUF_NMEM="$NMEM"
export SINGULARITYENV_MUF_KNOT=2
$SING /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/transition_knots/incontainer_5knot.sh \
   python3 -u /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/transition_knots/prepare_cache_5knot.py \
   --card "$CARD" \
   --base-conf "$BASE/base.conf" \
   -o "$BASE/$TAG" --outname cache \
   --subset '*/13,14,15,16,17,18,19,20' \
   --threads "$THREADS" --pdf-eig 0
