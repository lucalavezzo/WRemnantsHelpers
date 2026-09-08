#!/bin/bash
# Container entry for the 260908 physical-lambda reco toy.
#
# LIBRARY: the SAME frozen snapshot the failing 2026-09-07 run used --
#   /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot
#   SCETlib b66f8de, libscet-qT.so md5 71b5e68a0cfed89326ff4ed521d37300.
# This run is a controlled repeat of 260907-reco-fit-speed TOYE210_B with ONLY
# the NP priors changed, so the library MUST be identical; the newer e84f0b3
# (adopted in a sibling task) would confound the comparison.
#
# PYTHON: lib/scetlib_tf.py is a copy of that task's ab/B file -- the FIXED
# model, i.e. the snapshot's file plus the 2-line hvp zero-seed skip
# (md5 a2081a17a57669a958cda2acdc818cc8; the unfixed arm A is 20378cd4...).
#
# PROVENANCE NOTE, 2026-09-08: the working-tree copy of lib/scetlib_tf.py is now
# md5 e60ed9304569bfb496988ef729885469, not a2081a17 as stated above.  A
# `git add -A` in WRemnantsHelpers staged this file and the pre-commit hook ran
# black over it.  The a2081a17 bytes are not recoverable (no copy survived on
# disk).  The CODE is unchanged: diffed against an independent reconstruction
# (frozen snapshot + SCETlib MR !11 hunk, black-normalised) the only differences
# are 20 lines of docstring text, zero code lines, and the functional gate
# `if not vv.any():` is present.  Every run log in this directory printing
# a2081a17 is the correct record of what actually ran.  pyproject.toml now
# force-excludes studies/**/{lib,ab}/ so this cannot recur.
set -e
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-physical-lambda-toy
source /opt/venv/bin/activate
source /home/submit/lavezzo/alphaS/WRemnants/setup.sh > /dev/null
export SCETLIB_BUILD=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/build
source /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/setup.sh > /dev/null
export PYTHONPATH="$D/lib:$PYTHONPATH"
export PYTHONDONTWRITEBYTECODE=1
cd /home/submit/lavezzo/alphaS/WRemnants
python3 -c "
import scetlib_tf,inspect,hashlib,os
p=inspect.getsourcefile(scetlib_tf); src=open(p,'rb').read()
print('[env] scetlib_tf', p, 'md5', hashlib.md5(src).hexdigest())
print('[env] zero-skip present (FIXED model):', b'if not vv.any():' in src)
lib=os.environ['SCETLIB_BUILD']+'/lib/libscet-qT.so'
print('[env] libscet-qT.so md5', hashlib.md5(open(lib,'rb').read()).hexdigest())
"
exec "$@"
