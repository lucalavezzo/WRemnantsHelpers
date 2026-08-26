#!/bin/bash
# One (x2, knot) point of the isolated interpolation-error A/B. No cache: this
# builds rules + the muF pair live on five qT bins.
set -e
X2="$1"; KNOT="$2"; TAG="$3"
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/interp
BASE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest"
$SING /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/knot_scan/incontainer_knots.sh \
   python3 -u /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/knot_scan/knot_interp_error.py \
   --base "$BASE" --x2 "$X2" --knot "$KNOT" --threads 24 -o "$OUT/$TAG.json"
