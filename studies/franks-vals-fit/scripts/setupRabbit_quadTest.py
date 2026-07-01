#!/usr/bin/env python3
"""Tiny wrapper around setupRabbit.py that monkey-patches
Datagroups.addSystematic so the default symmetrization for any NP
nuisance (name starts with "scetlibNP") becomes "quadratic" instead
of the framework default "average".

This bypasses the fact that the --symmetrizeTheoryUnc=quadratic flag
in setupRabbit.py never reaches the NP-adder calls in
rabbit_theory_helper.py (those rely on addSystematic's own default).

Usage: identical to setupRabbit.py — argv pass-through. Run with the
same flags the chain wrappers normally pass to setupRabbit.py.
"""

import runpy
import sys

# Monkey-patch BEFORE the setupRabbit script runs so its add_*_uncertainties
# calls see the new default.
from wremnants.postprocessing.datagroups.datagroups import Datagroups

_orig_addSystematic = Datagroups.addSystematic


def _addSystematic_quadNP(self, *args, **kwargs):
    name = kwargs.get("name", "")
    if (
        isinstance(name, str)
        and name.startswith("scetlibNP")
        and "symmetrize" not in kwargs
    ):
        kwargs["symmetrize"] = "quadratic"
    return _orig_addSystematic(self, *args, **kwargs)


Datagroups.addSystematic = _addSystematic_quadNP

# Path to the upstream setupRabbit.py. We resolve via WREM_BASE so this
# follows future framework moves.
import os

WREM_BASE = os.environ.get("WREM_BASE")
if not WREM_BASE:
    sys.exit("WREM_BASE not set; source setup.sh first.")
SETUP = os.path.join(WREM_BASE, "scripts/rabbit/setupRabbit.py")

# Run setupRabbit.py under __name__ == "__main__" so its argparse + body fire.
runpy.run_path(SETUP, run_name="__main__")
