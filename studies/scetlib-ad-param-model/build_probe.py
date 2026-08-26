#!/usr/bin/env python3
"""Run a builder as __main__ and report what it dragged in.

The point of the measurement: prepare_cache_for_card never calls TensorFlow,
but it used to import it (through xsec_backend._import_scetlib, which pulled
scetlib_tf for a save that needs only numpy). TF costs ~800 MB and one
tf_Compute thread per core, charged against the 32768-threads-per-user ceiling
that the build's own parallelism is already spending.
"""
import os
import resource
import runpy
import sys

builder = sys.argv[1]
sys.argv = [os.path.basename(builder)] + sys.argv[2:]
peak_threads = 0
try:
    runpy.run_path(builder, run_name="__main__")
except SystemExit as e:
    if e.code:
        raise
print("=== build_probe ===")
print("tensorflow imported :", "tensorflow" in sys.modules)
print("scetlib_tf imported :", "scetlib_tf" in sys.modules)
print("modules             :", len(sys.modules))
print("peak RSS MB         : %.1f" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e3))
print("threads now         :", len(os.listdir("/proc/self/task")))
