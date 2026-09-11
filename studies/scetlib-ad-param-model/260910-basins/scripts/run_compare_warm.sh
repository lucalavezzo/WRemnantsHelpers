#!/bin/bash
# Thin driver for the PURPOSE-BUILT tool
#   ../../260908-fit-770/compare_warm.py
# written 2026-09-08 for exactly this question and never used until now.  It is
# invoked, not copied: it already prints only differences in units of sigma and
# never an alpha_s value, which is what makes it safe on blinded data.
#
# The only thing added here is a /tmp copy of each fitresult before reading.
# Another session runs saturated-projection jobs (--externalPostfit) against
# these same 110 MB files and h5py then fails with BlockingIOError (errno 11);
# `cp` takes no HDF5 lock and cannot perturb the other job.  Do NOT set
# HDF5_USE_FILE_LOCKING=FALSE instead -- tried in ../260910-spectral-precond,
# and it converts a clean BlockingIOError into a silently half-consistent read.
set -e
T=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260910-basins
TOOL=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770/compare_warm.py
S=/tmp/basins_warm
mkdir -p $S
cp -n "$1" $S/ 2>/dev/null || true
cp -n "$2" $S/ 2>/dev/null || true
exec python3 $TOOL $S/$(basename "$1") $S/$(basename "$2") --json "$3" --top 20
