#!/bin/bash
# Full readout of the ASIMOVREF arm, in the ONLY order that is honest:
# convergence first, sigma second.
#
#   usage: run_readout.sh <fitresult.hdf5> <fit.log>
#
# Part 1 is this task's own readout_convergence.py (exit status, minimiser
# verdict, EDM, Hessian spectrum, Cholesky, chi2, timings).
# Part 2 is the BLINDING task's read_postfit.py, reused verbatim rather than
# reimplemented, so that sigma(alpha_s) here and sigma(alpha_s) in the blinded
# arm come out of the same code path and the same 0.002 width conversion. That
# script is read and RUN, never edited -- it belongs to 260910-blinding.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-asimov-ref
B=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-blinding
echo "######## PART 1: CONVERGENCE (read this before any sigma)"
python3 -u $T/scripts/readout_convergence.py "$1" "$2"
echo
echo "######## PART 2: PARAMETERS AND sigma(alpha_s)  [read_postfit.py, 260910-blinding]"
python3 -u $B/scripts/read_postfit.py "$1"
echo READOUT_DONE
