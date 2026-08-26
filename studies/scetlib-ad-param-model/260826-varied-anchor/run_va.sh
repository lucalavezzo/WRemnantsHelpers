#!/bin/bash
# Four independent processes, each ONE cache built at ONE anchor.
#   nomA  the nominal anchor (x2 = 0.6)          + the live runcard reference there
#   nomB  the SAME runcard, second independent build -> the in-situ build-to-build floor
#   varA  the x2 = 0.35 anchor                   + the live runcard reference there
#   x13A  the x1,x3 = 0.3,0.9 anchor             + the live runcard reference there
set -u
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260826-varied-anchor
B=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/knot_scan/base.conf
IMG=/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
SING="singularity exec --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ $IMG"
export TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2
go () {
  tag="$1"; shift
  $SING $D/incontainer_va.sh python3 -u $D/varied_anchor.py --base "$B" \
    --knot 2.0 --threads 8 --tag "$tag" -o "$D/$tag.json" "$@" \
    > "$D/$tag.log" 2>&1 &
}
go nomA --anchor='-,-,-'     --eval='-,-,-'     --eval='-,0.35,-' --eval='0.3,-,0.9' --direct --seed 4242
go nomB --anchor='-,-,-'     --eval='-,-,-'     --eval='-,0.35,-' --eval='0.3,-,0.9'           --seed 9999
go varA --anchor='-,0.35,-'  --eval='-,0.35,-'  --eval='-,0.6,-'                     --direct --seed 4242
go x13A --anchor='0.3,-,0.9' --eval='0.3,-,0.9' --eval='0.2,-,1.0'                   --direct --seed 4242
wait
echo "VA QUEUE DONE $(date)"
