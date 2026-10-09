#!/usr/bin/env bash
# trace.sh [PF] [N]: last N iterations of a TC fit as "it loss loss-XW(nopen) optimality constr_violation barrier tr_radius"
# XWSTIFF penalty-free NLL = 371.3283536451 (compare.py); XL4ZSTIFF = +0.9549, CMR1B = +0.4300 on that scale.
PF=${1:-TCC1}; N=${2:-15}
L=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/trust-constr-nominal/261006-tc-from-C/logs/$PF.log
sed 's/\x1b\[[0-9;]*m//g' $L | awk '/Iteration [0-9]+:/{it=$3; sub(":","",it); loss=$5} /trust-constr: opt/{printf "%4d %.6f %+9.5f %.3e %.2e %.2e %.2e\n", it, loss, loss-371.3283536451, $4, $6, $8, $10}' | tail -n $N
