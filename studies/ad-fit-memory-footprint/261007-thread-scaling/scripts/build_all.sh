#!/bin/bash
for t in 128 16 32 64 256; do python3 /home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/ad-fit-memory-footprint/261007-thread-scaling/scripts/build_cmd.py $t 2>&1 | grep -v Warning; done
