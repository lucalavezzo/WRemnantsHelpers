#!/usr/bin/env python3
"""T4 step 0 (ONE gated cache load): NLL cost of the census starts, split NP draw vs non-NP kick.

Fitter rebuilt from NOMSTIFF's OWN meta_info command (tau 8, -r NPDampingWall NPDampingMapping margin=0),
minus -o / --snapshot* / --externalPostfit, exactly as rabbit_fit.main() builds it: tau + regularizers before the
first trace, defaultassign() (arms the wall), set_nobs(data), blinding offsets ARMED (never disarmed).
Pattern: ../../260930-random-starts/scripts/seed_nll_check.py (adapted: the reference's own wall is already
margin 0, so its own regularizer is used for the penalty instead of a second margin-0 copy).

Gate: reduced_nll at NOMSTIFF reproduces its stored nllvalreduced.
Then per seed file: load_fitresult(seed) -> reduced_nll and its components (ln data, lc constraints, lbeta BB,
lpen wall), max|grad|. Only DIFFERENCES to NOMSTIFF are printed/saved. No alphaS value is printed.
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
    print("[step0] replaying the stored command minus", dropped, flush=True)
    args = rabbit_fit.make_parser().parse_args(argv)
    assert args.regularizationStrength == 8.0, args.regularizationStrength
    assert any("margin=0" in m for m in args.regularization[0][2:]), args.regularization
    wlogging.setup_logger("step0", args.verbose, args.noColorLogger)
    nll_stored = float(io_tools.get_fitresult(a.ref, None)["nllvalreduced"])

    t0 = time.time()
    indata = inputdata.FitInputData(args.filename, args.pseudoData, host_memory=False)
    param_model = ph.load_models(args.paramModel, indata, **vars(args))
    print(f"[step0] cache loaded + model built in {time.time()-t0:.0f} s", flush=True)
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
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)
    f.defaultassign()
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)

    comps = tf.function(
        lambda: f._compute_nll_components(profile=True, full_nll=False)[:4]
    )

    def evaluate(path):
        t = time.time()
        f.load_fitresult(path, None, profile=True)
        nll = float(f.reduced_nll().numpy())
        ln, lc, lb, lp = comps()
        try:
            _, g = f.loss_val_grad()
            g = g.numpy()
            gfin, gmax = bool(np.all(np.isfinite(g))), float(np.max(np.abs(g)))
        except Exception as e:  # report, do not hide
            gfin, gmax = None, f"{type(e).__name__}: {e}"
        return dict(
            nll=nll,
            finite=bool(np.isfinite(nll)),
            ln=float(ln),
            lc=float(lc),
            lbeta=float(lb) if lb is not None else 0.0,
            lpen=float(lp) if lp is not None else 0.0,
            grad_finite=gfin,
            grad_max=gmax,
            eval_s=time.time() - t,
        )

    out = {}
    r = evaluate(a.ref)
    r["gate_diff_vs_stored"] = r["nll"] - nll_stored
    print(
        f"[gate] NOMSTIFF: reduced_nll - stored = {r['gate_diff_vs_stored']:+.3e}  wall pen {r['lpen']:.3g}",
        flush=True,
    )
    out["reference"] = r
    for p in a.seeds:
        s = evaluate(p)
        for k in ("nll", "ln", "lc", "lbeta", "lpen"):
            s[f"d_{k}"] = s[k] - r[k]
        key = (
            os.path.relpath(p, os.path.dirname(os.path.dirname(p)))
            if "step0" in p
            else os.path.basename(p)
        )
        out[key] = s
        print(
            f"[seed] {key}: finite={s['finite']} dNLL={s['d_nll']:+.2f} "
            f"(d_ln={s['d_ln']:+.2f} d_lc={s['d_lc']:+.2f} d_lbeta={s['d_lbeta']:+.2f} d_lpen={s['d_lpen']:+.3g}) "
            f"grad finite={s['grad_finite']} |grad|max={s['grad_max']:.3g} ({s['eval_s']:.0f} s)",
            flush=True,
        )
    for v in out.values():
        for k in ("nll", "ln", "lc", "lbeta", "lpen"):
            v.pop(k, None)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"[step0] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
