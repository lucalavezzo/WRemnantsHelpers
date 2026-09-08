#!/bin/bash
# Container entry for 260908-fit-770.
#
# LIBRARY: the frozen VALIDATED snapshot
#   /work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot
#   SCETlib b66f8de, libscet-qT.so md5 71b5e68a0cfed89326ff4ed521d37300.
# NOT e84f0b3: its adoption is unresolved (it drops MR !8 and MR !9 -- see
# 260907-adopt-e84f0b3/LOGBOOK.md), and the 770-bin cache and both cards were
# validated against b66f8de.  Same library as 260907-reco-fit-speed and
# 260908-physical-lambda-toy, so every number here is directly comparable to
# theirs.
#
# PYTHON: lib/scetlib_tf.py is the FIXED model -- the snapshot's file plus the
# 2-line hvp zero-seed skip (md5 a2081a17a57669a958cda2acdc818cc8).  Without it
# the postfit Hessian pass costs ~77x more (measured).
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
D=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/scetlib-ad-param-model/260908-fit-770
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
# Stamp the FITTER too.  SCETlib and the model file are pinned by md5 above, but
# rabbit was not -- and rabbit is where the blinding rule, the toy-throw
# semantics and the EDM definition live.  There are ~10 rabbit checkouts on this
# filesystem, so "which rabbit ran" must not be recoverable only by chaining
# run.sh -> incontainer.sh -> WRemnants/setup.sh.  (Gap found by adversarial
# review 2026-09-08; the runs already logged in this task predate this line, and
# their rabbit is recorded in the logbook instead.)
echo "[env] rabbit $WREM_BASE/rabbit @ $(git -C $WREM_BASE/rabbit rev-parse --short HEAD 2>/dev/null || echo 'no git') ($(git -C $WREM_BASE/rabbit rev-parse --abbrev-ref HEAD 2>/dev/null))"
exec "$@"
