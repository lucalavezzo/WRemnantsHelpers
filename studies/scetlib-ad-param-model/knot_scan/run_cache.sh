#!/bin/bash
# One arm of the knot-spacing A/B: build a 10-bin subset cache at a given muF
# knot factor. Everything except MUF_KNOT is identical between arms, and both
# arms run the SAME binary (the factor defaults to 2, so arm "knot2" is the
# unpatched behaviour bit for bit).
set -e
KNOT="$1"; TAG="$2"
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan
CARD=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260820_Z_2D_card_scetlib_ad/ZMassDilepton_ptll_yll_realdata/ZMassDilepton.hdf5
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
export SINGULARITYENV_MUF_KNOT="$KNOT"
$SING /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/knot_scan/incontainer_knots.sh \
   python3 -u /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/knot_scan/prepare_cache_knots.py \
   --card "$CARD" \
   --base-conf "$BASE/base.conf" \
   -o "$BASE/$TAG" --outname cache \
   --subset '0,1/16,17,18,19,20' \
   --threads 32 --pdf-eig 0
