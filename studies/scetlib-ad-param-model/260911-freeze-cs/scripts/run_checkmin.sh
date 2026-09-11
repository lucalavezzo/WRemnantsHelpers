#!/bin/bash
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
exec $T/scripts/run.sh $T/logs/checkmin_$(date +%y%m%d_%H%M%S).log python3 $T/scripts/check_minimum_frz.py "$@"
