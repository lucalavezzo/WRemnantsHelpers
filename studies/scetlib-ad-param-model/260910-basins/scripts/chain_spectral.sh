#!/bin/bash
# Wait for WARMPLAIN to exit, then launch the spectral warm restart.
# Staggered on purpose: each of these fits peaks at ~185 GiB resident and
# another session already holds ~56 GiB, so five at once would be ~980 GiB of
# 1447 with 663 GiB of it currently page cache. Four concurrent is the ceiling
# used here.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-basins
L=$(cat $T/logs/LATEST_WARMPLAIN)
until grep -qE "^\[run\] DONE rc=" "$L"; do sleep 20; done
exec $T/scripts/launch_warm.sh spectral
