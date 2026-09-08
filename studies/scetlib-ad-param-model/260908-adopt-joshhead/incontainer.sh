#!/bin/bash
# Josh's head (dce84b1) + our MR !11 (8e92c14) == branch hvp-fast-covariance.
# libscet-qT.so md5 4d658b6d1b3589c81c6fa977919d5e13
# The VALIDATED library for comparison is b66f8de / md5 71b5e68a0cfed89326ff4ed521d37300.
set -e
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-joshhead-260908/build
source /work/submit/lavezzo/alphaS/scetlib-ad-joshhead-260908/setup.sh > /dev/null
cd /home/submit/lavezzo/alphaS/WRemnants
python3 -c "
import os, hashlib
lib = os.environ['SCETLIB_BUILD'] + '/lib/libscet-qT.so'
print('[env] libscet-qT.so md5', hashlib.md5(open(lib,'rb').read()).hexdigest())
"
exec "$@"
