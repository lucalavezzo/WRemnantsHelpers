import os
import pickle
import matplotlib.pyplot as plt
import numpy as np
import argparse
import mplhep as hep

hep.style.use(hep.style.ROOT)

parser = argparse.ArgumentParser()
parser.add_argument("input_file", type=str)
parser.add_argument("-o", "--outdir", required=True, type=str)
parser.add_argument("--selectFirstKnots", default=None, type=int)
args = parser.parse_args()

with open(args.input_file, "rb") as f:
    inputs = pickle.load(f)

rmss = [i[1] for i in inputs]
lams = [i[0][0] for i in inputs]
knotss = [i[0][1] for i in inputs]

# plot results as function of lambda for different values of knots per axis
fig = plt.figure()
ax = fig.add_subplot()

lambs_by_knots = []
lambs_rmss = []
ref_knots = []
for lam, knots, rms in zip(lams, knotss, rmss):
    if args.selectFirstKnots:
        if knots[0] != args.selectFirstKnots:
            continue
    if knots not in ref_knots:
        ref_knots.append(knots)
        lambs_by_knots.append([lam])
        lambs_rmss.append([rms])
    else:
        i = [j for j, ref in enumerate(ref_knots) if ref == knots]
        assert len(i) == 1
        i = i[0]
        lambs_by_knots[i].append(lam)
        lambs_rmss[i].append(rms)
for x, y, label in zip(lambs_by_knots, lambs_rmss, ref_knots):
    print(x, y, label)
    ax.scatter(x, y, label=label)
    ax.plot(x, y)
ax.set_xlabel(r"$\lambda$")
ax.set_ylabel("RMS")
ax.legend(loc=(1.01, 0))
ax.set_yscale("log")
ax.set_xscale("log")
fig.tight_layout()
fig.savefig(
    os.path.join(
        args.outdir, args.input_file.replace(".pkl", "") + "_knotsByLambda_" + ".pdf"
    ),
    bbox_inches="tight",
)
fig.savefig(
    os.path.join(
        args.outdir, args.input_file.replace(".pkl", "") + "_knotsByLambda_" + ".png"
    ),
    bbox_inches="tight",
)
