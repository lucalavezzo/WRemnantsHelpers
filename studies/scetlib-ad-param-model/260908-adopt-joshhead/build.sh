#!/bin/bash
# Build Josh's head (dce84b1) + our MR !11 (8e92c14) = branch hvp-fast-covariance.
set -e
W=/work/submit/lavezzo/alphaS/scetlib-ad-joshhead-260908
source /opt/venv/bin/activate
cd $W
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build -j 48
echo "BUILD OK"
ls -la build/lib/libscet-qT.so
md5sum build/lib/libscet-qT.so
