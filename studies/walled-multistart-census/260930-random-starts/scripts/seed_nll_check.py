#!/usr/bin/env python3
"""Validation 4 (ONE gated cache load): the seeds load into the real walled nominal Fitter
through Fitter.load_fitresult (the --externalPostfit path) and give a finite NLL and gradient.

Fitter rebuilt from LATL4ZY35WALLWARM's own meta_info command, exactly as rabbit_fit.main()
does it (tau + regularizers before the first trace; defaultassign -> arm; set_nobs(data);
blinding offsets ARMED and never disarmed). Pattern: 260930-wall-margin-keyword/scripts/
margin_loss_gate.py and walled-two-minima/260930-walled-chord/scripts/walled_common.py.

Gate: reduced_nll at the reference postfit reproduces its stored nllvalreduced.
Then per seed: load_fitresult(seed) -> reduced_nll, its components, the margin-0 wall penalty
(eager), and |grad| from the fitter's own loss_val_grad. Reported RELATIVE to the reference
(differences only). No alphaS value is printed.
"""

import argparse
import json
import os

os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=true")

import shlex  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402

RABBIT_BIN = "/home/submit/lavezzo/alphaS/WRemnants/rabbit/bin"
if RABBIT_BIN not in sys.path:
    sys.path.insert(0, RABBIT_BIN)

import rabbit_fit  # noqa: E402
from rabbit import fitter as rfitter  # noqa: E402
from rabbit import inputdata, io_tools  # noqa: E402
from rabbit.mappings import helpers as mh  # noqa: E402
from rabbit.param_models import helpers as ph  # noqa: E402
from rabbit.regularization import helpers as rh  # noqa: E402
from wums import logging as wlogging  # noqa: E402

DROP_WITH_VALUE = {
    "--snapshotFile",
    "--snapshotInterval",
    "-o",
    "--outpath",
    "--externalPostfit",
}


def argv_from_meta(path, outdir):
    _, meta = io_tools.get_fitresult(path, None, meta=True)
    cmd = shlex.split(meta["meta_info"]["command"])
    out, i, dropped = [], 1, []
    while i < len(cmd):
        if cmd[i] in DROP_WITH_VALUE:
            dropped.append(cmd[i : i + 2])
            i += 2
            continue
        out.append(cmd[i])
        i += 1
    return out + ["-o", outdir], dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--seeds", nargs="+", required=True)
    ap.add_argument("--out", required=True, help="json output")
    a = ap.parse_args()

    argv, dropped = argv_from_meta(a.ref, "/tmp")
    print("[seedcheck] replaying the stored command minus", dropped, flush=True)
    args = rabbit_fit.make_parser().parse_args(argv)
    wlogging.setup_logger("seedcheck", args.verbose, args.noColorLogger)
    nll_stored = float(io_tools.get_fitresult(a.ref, None)["nllvalreduced"])

    t0 = time.time()
    indata = inputdata.FitInputData(args.filename, args.pseudoData, host_memory=False)
    param_model = ph.load_models(args.paramModel, indata, **vars(args))
    print(
        f"[seedcheck] cache loaded + model built in {time.time()-t0:.0f} s", flush=True
    )
    f = rfitter.make_fitter(
        indata,
        param_model,
        args,
        do_blinding=True,
        globalImpactsFromJVP=not args.globalImpactsDisableJVP,
    )
    f.tau.assign(args.regularizationStrength)
    regs = []
    for margs in args.regularization:
        regs.append(
            rh.load_regularizer(
                margs[0],
                mh.load_mapping(margs[1], indata, *margs[2:]),
                dtype=indata.dtype,
            )
        )
    f.regularizers = regs
    margs = args.regularization[0]
    reg0 = rh.load_regularizer(
        margs[0],
        mh.load_mapping(margs[1], indata, *margs[2:], "margin=0"),
        dtype=indata.dtype,
    )
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)
    f.defaultassign()
    reg0.set_expectations(f.get_x(), None, parms=f.parms)
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)

    comps = tf.function(
        lambda: f._compute_nll_components(profile=True, full_nll=False)[:4]
    )

    def evaluate(path):
        f.load_fitresult(path, None, profile=True)
        nll = float(f.reduced_nll().numpy())
        ln, lc, lb, lp = comps()
        pen0 = float(reg0.compute_nll_penalty(f.get_x(), None).numpy())
        try:
            _, g = f.loss_val_grad()
            g = g.numpy()
            gfin, gmax, gnorm = (
                bool(np.all(np.isfinite(g))),
                float(np.max(np.abs(g))),
                float(np.linalg.norm(g)),
            )
        except Exception as e:  # report, do not hide
            gfin, gmax, gnorm = None, None, f"{type(e).__name__}: {e}"
        return dict(
            nll=nll,
            finite=bool(np.isfinite(nll)),
            ln=float(ln),
            lc=float(lc),
            lbeta=float(lb) if lb is not None else None,
            lpen_default=float(lp) if lp is not None else None,
            pen_margin0_raw=pen0,
            grad_finite=gfin,
            grad_max=gmax,
            grad_norm=gnorm,
        )

    out = {}
    r = evaluate(a.ref)
    r["gate_diff_vs_stored"] = r["nll"] - nll_stored
    print(
        f"[gate] reference: reduced_nll - stored = {r['gate_diff_vs_stored']:+.3e}",
        flush=True,
    )
    out["reference"] = r
    for p in a.seeds:
        s = evaluate(p)
        for k in ("nll", "ln", "lc", "lbeta"):
            if s[k] is not None and r[k] is not None:
                s[f"d_{k}"] = s[k] - r[k]
        out[os.path.basename(p)] = s
        print(
            f"[seed] {os.path.basename(p)}: finite={s['finite']} dNLL={s['d_nll']:+.2f} "
            f"(d_ln={s['d_ln']:+.2f} d_lc={s['d_lc']:+.2f} d_lbeta={s.get('d_lbeta', float('nan')):+.2f}) "
            f"wall pen(default)={s['lpen_default']:.3g} pen(margin0,raw)={s['pen_margin0_raw']:.3g} "
            f"grad finite={s['grad_finite']} |grad|max={s['grad_max']}",
            flush=True,
        )
    # absolute NLL values are not alphaS; still, keep only differences + gate in the json
    for v in out.values():
        v.pop("nll", None)
        for k in ("ln", "lc", "lbeta"):
            v.pop(k, None)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"[seedcheck] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
