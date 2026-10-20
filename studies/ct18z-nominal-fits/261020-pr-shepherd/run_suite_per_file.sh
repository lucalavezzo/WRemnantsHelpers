#!/bin/bash
# CI-style rabbit suite: each test file in its own process (as WMass/rabbit main.yml does).
# usage: run_suite_per_file.sh <worktree> <logprefix>   (run inside the container, worktree on PYTHONPATH)
W=$1; P=$2
cd $W
failed=""
for f in tests/test_*.py; do
  python -m pytest "$f" -q -p no:cacheprovider > ${P}_$(basename $f .py).log 2>&1
  rc=$?
  echo "$f rc=$rc $(tail -1 ${P}_$(basename $f .py).log)"
  [ $rc -ne 0 ] && [ $rc -ne 5 ] && failed="$failed $f"
done
echo "FAILED:${failed:- none}"
