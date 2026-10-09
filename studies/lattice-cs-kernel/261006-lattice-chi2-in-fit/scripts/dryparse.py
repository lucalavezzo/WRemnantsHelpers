"""Dry check of a built command: rabbit_fit's own parser accepts it and both -r regularizers load on the card (no cache)."""

import shlex
import sys

sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants/rabbit/bin")
import rabbit_fit  # noqa: E402
import tensorflow as tf  # noqa: E402
from rabbit import inputdata  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402

toks = shlex.split(open(sys.argv[1]).read())
args = rabbit_fit.make_parser().parse_args(toks[1:])
print(
    "regularizationStrength",
    args.regularizationStrength,
    "| -r entries:",
    len(args.regularization),
)
indata = inputdata.FitInputData(args.filename)
print("external terms on card:", getattr(indata, "external_terms", None))
for margs in args.regularization:
    reg = rh.load_regularizer(
        margs[0], mh.load_mapping(margs[1], indata, *margs[2:]), dtype=tf.float64
    )
    print("loaded", type(reg).__name__, margs[2:])
