#!/usr/bin/env bash
# The fit for this task. Thin: standard entry points only.
#   bin/run          detach + timestamped log
#   agent_setup.sh   container + env (fitterAD.sh needs WREM_BASE + SCETLIB_BUILD)
#   fitterAD.sh      the fit itself
#
# --scetlib authval is REQUIRED here: the 260827 cache is rules v8 / fo v6,
# below the current build's kRuleVersionMin = 10, so only the frozen snapshot
# can read it.
#
# usage: fit.sh <card> <postfix> <outdir> [extra rabbit/model args...]
#
# Extra args are appended to fitterAD.sh's -f. Note how fitterAD.sh builds its
# command: -f lands at the END, after the --paramModel positionals, so a token
# WITHOUT a leading dash (threads=128) becomes a MODEL arg while a dashed one
# (-v 4, --minimizerMethod X) is parsed as a rabbit option. Order accordingly:
# model args first.
#
# threads=128 is passed by default to keep one fit from taking ~490 cores (the
# measured note says more threads do not help reco anyway), so two fits can run
# side by side on the 768-core node.
set -e
H=/home/submit/lavezzo/alphaS/WRemnantsHelpers
# The hvp zero-seed skip (`if not vv.any(): return zeros`) is REQUIRED: without
# it every Hessian-vector product with a zero seed falls through to a full
# SCETlib evaluation for a result that is identically zero. A dense Hessian
# asks for one hvp per fit parameter (3721 here) of which ~3675 are zero
# directions, so unpatched it costs ~7.75 h instead of ~5 min.
#
# It lives UPSTREAM in scetlib (scetlib-cms 1d8ccf9 and the 260914 pin, both
# hvp sites). It was missing only from the frozen 260827 authval snapshot, so
# on 2026-09-17 it was backported there (original kept alongside as
# scetlib_tf.py.orig_pre_hvpshortcut). Hence no --prepend-pythonpath any more.
AUTHVAL_PY=/work/submit/lavezzo/alphaS/scetlib-ad-authval-260827/scetlib_snapshot/py/scetlib_tf.py
grep -q "if not vv.any():" "$AUTHVAL_PY" || { echo "fit.sh: $AUTHVAL_PY lacks the hvp zero-seed skip"; exit 2; }

CACHE=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_corrgrid_260827/merged_full
CARD=$1; POSTFIX=$2; OUT=$3; shift 3
exec "$H/agent_setup.sh" --scetlib authval -- \
  "$H/workflows/fitterAD.sh" "$CARD" -c "$CACHE" -o "$OUT" -p "$POSTFIX" \
    -f "threads=128 -v 4 $*"
