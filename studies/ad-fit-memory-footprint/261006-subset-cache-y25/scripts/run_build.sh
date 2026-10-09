#!/usr/bin/env bash
# run_build.sh: build the |Y|<=2.5 subset cache, then extract its flat rules file for the fast path.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
T=$H/studies/ad-fit-memory-footprint/261006-subset-cache-y25
SRC=/scratch/submit/cms/alphaS/ad_scetlib_caches/pdf62_y35_260921/merged_full_bin0xzero
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25
echo "[run] $(date -Is) host=$(hostname) scetlib=$(git -C $H/../WRemnants/scetlib-cms rev-parse --short HEAD) WRemnants=$(git -C $H/../WRemnants rev-parse --short HEAD) build_md5=$(md5sum $T/scripts/build_subset_cache.py | cut -c1-32) io_md5=$(md5sum $T/scripts/cache_io.py | cut -c1-32)"
$H/agent_setup.sh --scetlib current -- python3 $T/scripts/build_subset_cache.py --src $SRC --out $OUT --ymax 2.5 || { echo "[run] build FAILED"; exit 1; }
echo "[run] $(date -Is) extracting rules"
$H/agent_setup.sh --scetlib current -- python3 $H/../WRemnants/scripts/rabbit/scetlib_ad/extract_cache_rules.py $OUT/cache.npz || { echo "[run] extract FAILED"; exit 1; }
echo "[run] $(date -Is) md5 of the extracted rules"
md5sum $OUT/cache.rules.bin
cat $OUT/rules_payload.md5
echo "[run] $(date -Is) DONE"
