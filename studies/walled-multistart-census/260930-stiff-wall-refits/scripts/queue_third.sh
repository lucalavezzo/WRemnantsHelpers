#!/usr/bin/env bash
# Wait until fewer than 2 of our STIFF fits are alive (comm == python3, no self-match), then launch XL4ZSTIFF.
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/walled-multistart-census/260930-stiff-wall-refits
n_alive() { ps -eo comm=,args= | awk '$1=="python3" && /--postfix (NOM|XW)STIFF/' | wc -l; }
sleep 600   # let NOM/XW get through their loads first
while [ "$(n_alive)" -ge 2 ]; do sleep 300; done
echo "[queue_third] $(date -Is) alive=$(n_alive): launching XL4ZSTIFF"
bash "$T/scripts/launch.sh" XL4ZSTIFF
