#!/usr/bin/env bash
# write_provenance.sh: PROVENANCE.txt + README.txt for the |Y|<=2.5 subset cache (after build + extract + static validation).
set -euo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ad-fit-memory-footprint/261006-subset-cache-y25
SRC=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero
CEPHSRC=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921/merged_full_bin0xzero
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25
SRCMD5=$(cut -c1-32 $T/logs/src_npz.md5)
NPZMD5=$(md5sum $OUT/cache.npz | cut -c1-32)
RULESMD5=$(grep -oE "^[0-9a-f]{32}  .*cache.rules.bin$" $T/logs/extract.log | head -1 | cut -c1-32)
cat > $OUT/PROVENANCE.txt <<EOF
|Y| <= 2.5 SUBSET of the quick-patched y35 AD cache (770 of its 1050 bins), made $(date -Is) by $USER.
source        $SRC/cache.npz  (md5 $SRCMD5; == the ceph master $CEPHSRC/cache.npz md5 e2e3a706e035ed2efabcbe6ad33afdfc)
source rules  $SRC/cache.rules.bin  (crc32 $(python3 -c "import json;print(json.load(open('$SRC/cache.rules.json'))['crc32'])") of the source rules.npy member)
SCETlib       WRemnants/scetlib-cms @ $(git -C $H/../WRemnants/scetlib-cms rev-parse HEAD) (scetlib_cache.parse_fo_blob / parse_rule_blob used; rules v13 / fo v14 / format 3)
script        $T/scripts/build_subset_cache.py (md5 $(md5sum $T/scripts/build_subset_cache.py | cut -c1-32)) + cache_io.py (md5 $(md5sum $T/scripts/cache_io.py | cut -c1-32))
              then WRemnants/scripts/rabbit/scetlib_ad/extract_cache_rules.py (WRemnants $(git -C $H/../WRemnants rev-parse --short HEAD)) for cache.rules.bin
cache.npz     md5 $NPZMD5
cache.rules.bin md5 $RULESMD5
validation    $T/LOGBOOK.md + $T/validate_static.json (30/30 static byte-identity checks PASS); NOMSTIFF --noFit replay in the logbook
EOF
cat > $OUT/README.txt <<EOF
|Y| <= 2.5 subset of pdf62_y35_260921/merged_full_bin0xzero (the qT[0,0.5] bin0xzero patch is KEPT: the form entries
are copied byte for byte). Rules and fixed-order blocks of the 770 kept bins are byte-identical to the source; the 280
bins with |Y| in [2.5, 3.5] are absent. cache.conf = the source runcard with Grid_Y cut at 2.5 (not in any fingerprint).
VALID ONLY for cards whose gen grid stays inside |Y| <= 2.5 (response auxiliary absYVGen up to 2.5, e.g. card A).
NOT valid for anything that needs |Y| > 2.5 (theory corrections / gen fits out to 3.5): the fold refuses missing bins.
Same reader as the source: in-tree scetlib-cms 2dd978a (agent_setup.sh --scetlib current) or the 2da973d/ca15aec pin.
Details: https://submit.mit.edu/~lavezzo/alphaS/studies/#ad-fit-memory-footprint/261006-subset-cache-y25
EOF
cat $OUT/PROVENANCE.txt $OUT/README.txt
