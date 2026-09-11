#!/bin/bash
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260911-freeze-cs
exec $T/scripts/run.sh $T/logs/gauss_$(date +%y%m%d_%H%M%S).log python3 $T/scripts/gaussian_predict.py "$@"
