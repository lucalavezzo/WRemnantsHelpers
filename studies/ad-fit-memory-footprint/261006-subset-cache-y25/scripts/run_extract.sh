#!/usr/bin/env bash
# run_extract.sh: the fast-path flat rules file for the subset cache, via WRemnants' extract_cache_rules.py.
set -uo pipefail
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
OUT=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/ad_scetlib_caches/pdf62_y35_260921_y25
echo "[run] $(date -Is) extracting rules (WRemnants $(git -C $H/../WRemnants rev-parse --short HEAD))"
$H/agent_setup.sh --scetlib current -- python3 $H/../WRemnants/scripts/rabbit/scetlib_ad/extract_cache_rules.py $OUT/cache.npz || { echo "[run] extract FAILED"; exit 1; }
echo "[run] $(date -Is) md5 of the extracted rules"
md5sum $OUT/cache.rules.bin
cat $OUT/rules_payload.md5
echo "[run] $(date -Is) DONE"
