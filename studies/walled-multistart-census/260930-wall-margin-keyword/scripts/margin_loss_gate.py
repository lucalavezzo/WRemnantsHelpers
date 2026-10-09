#!/usr/bin/env python3
"""Step 2 (one gated cache load): the margin= keyword on the REAL nominal lattice fit.

Rebuilds the rabbit Fitter of LATL4ZY35WALLWARM from its own meta_info command (same card, cache,
param model + fit_params/prior_sigmas, lattice term (in the card), freeze list, -r wall), exactly as
rabbit_fit.main() does (tau + regularizers BEFORE the first loss trace; defaultassign -> arm;
set_nobs(data); blinding offsets armed). Following walled-two-minima/260930-walled-chord
walled_common.py. Then, at the stored postfit x:

  (a) default wall (margin 5e-3), tau = 5: f.reduced_nll() vs the stored nllvalreduced;
  (b) margin=0 wall at tau = 8, built from the -r line + "margin=0" via rabbit's own loaders:
      loss(m0, tau8) - loss(default, tau5)  vs  e^16 pen(m0) - e^10 pen(5e-3),
      penalties computed EAGERLY with reg.compute_nll_penalty(x, None); every loss from a FRESH
      tf.function trace of f._compute_nll (the regularizer list is read at trace time);
      plus the unwalled base loss, so each walled loss is also checked as base + e^{2tau} pen;
  (c) per-condition coeff / penalty under both margins, i.e. which are active under margin 0;
  (d) the trace-time trap, demonstrated: f.reduced_nll() after swapping in the margin-0 wall still
      returns the margin-5e-3 loss (and tau, a tf.Variable, IS read at run time).

BLINDING: alphaS is blinded additively; the offsets are armed as in the fit and never disarmed.
Nothing about alphaS is printed. The NP lambdas are POUs (not blinded) and are printed physical.
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

tf.config.experimental.enable_op_determinism()

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

FR = (
    "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260928_lattice_y35_fits/"
    "fitresults_LATL4ZY35WALLWARM.hdf5"
)
# flags whose value is a path we must not touch, or that only matter for a minimisation
DROP_WITH_VALUE = {"--snapshotFile", "--snapshotInterval", "-o", "--outpath"}


def argv_from_meta(path, outdir):
    _, meta = io_tools.get_fitresult(path, None, meta=True)
    cmd = shlex.split(meta["meta_info"]["command"])
    assert cmd[0].endswith("rabbit_fit.py"), cmd[0]
    out, i, dropped = [], 1, []
    while i < len(cmd):
        if cmd[i] in DROP_WITH_VALUE:
            dropped.append(cmd[i : i + 2])
            i += 2
            continue
        out.append(cmd[i])
        i += 1
    return out + ["-o", outdir], dropped, meta["meta_info"]["command"]


def fresh_loss(f):
    """Loss from a FRESH trace, so the CURRENT f.regularizers is the one baked in."""
    fn = tf.function(lambda: f._compute_nll(full_nll=False))
    return float(fn().numpy())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--tau_hard", type=float, default=8.0)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    argv, dropped, cmd = argv_from_meta(FR, "/tmp")
    print("[margin_gate] replaying the stored command minus", dropped, flush=True)
    args = rabbit_fit.make_parser().parse_args(argv)
    wlogging.setup_logger("margin_gate", args.verbose, args.noColorLogger)
    assert args.regularizationStrength == 5.0
    assert len(args.regularization) == 1

    _, res_meta = io_tools.get_fitresult(FR, None, meta=True)
    res = io_tools.get_fitresult(FR, None)
    nll_stored = float(res["nllvalreduced"])

    t0 = time.time()
    indata = inputdata.FitInputData(args.filename, args.pseudoData, host_memory=False)
    param_model = ph.load_models(args.paramModel, indata, **vars(args))
    print(
        f"[margin_gate] cache loaded + model built in {time.time()-t0:.0f} s",
        flush=True,
    )
    f = rfitter.make_fitter(
        indata,
        param_model,
        args,
        do_blinding=True,  # -t 0 -> blinded
        globalImpactsFromJVP=not args.globalImpactsDisableJVP,
    )

    # exactly rabbit_fit.main(): tau + regularizers BEFORE any loss is traced
    f.tau.assign(args.regularizationStrength)
    margs = args.regularization[0]
    map5 = mh.load_mapping(margs[1], indata, *margs[2:])
    reg5 = rh.load_regularizer(margs[0], map5, dtype=indata.dtype)
    f.regularizers = [reg5]
    np.random.seed(args.seed)
    tf.random.set_seed(args.seed)
    f.defaultassign()  # -> arm_regularizers()
    f.set_nobs(f.indata.data_obs)
    f.set_blinding_offsets(blind=True)

    f.load_fitresult(FR, None, profile=True)
    x = f.get_x()

    # ---------------- (a)
    L5_traced = float(f.reduced_nll().numpy())
    print(
        f"[a] default wall tau=5: reduced_nll = {L5_traced:.11f} stored = {nll_stored:.11f} "
        f"diff = {L5_traced - nll_stored:+.3e}",
        flush=True,
    )

    # ---------------- margin-0 wall, built exactly as the -r line would build it
    map0 = mh.load_mapping(margs[1], indata, *margs[2:], "margin=0")
    reg0 = rh.load_regularizer(margs[0], map0, dtype=indata.dtype)
    assert reg0.margin == 0.0 and reg5.margin == 5e-3, (reg0.margin, reg5.margin)
    f.regularizers = [reg0]
    f.arm_regularizers()
    assert np.array_equal(f.get_x().numpy(), x.numpy()), "arming moved x"

    pen5 = float(reg5.compute_nll_penalty(x, None).numpy())
    pen0 = float(reg0.compute_nll_penalty(x, None).numpy())

    # (d) trap: the traced reduced_nll still carries reg5 (trace-time list), tau is runtime
    f.tau.assign(a.tau_hard)
    L_traced_after_swap_t8 = float(f.reduced_nll().numpy())

    # (b) fresh traces
    L0_t8 = fresh_loss(f)  # margin 0, tau 8
    f.regularizers = [reg5]
    f.arm_regularizers()
    f.tau.assign(args.regularizationStrength)
    L5_t5_fresh = fresh_loss(f)
    f.regularizers = []
    Lbase = fresh_loss(f)
    f.regularizers = [reg5]
    f.arm_regularizers()

    e10 = float(np.exp(2 * args.regularizationStrength))
    e16 = float(np.exp(2 * a.tau_hard))
    lhs = L0_t8 - L5_traced
    rhs = e16 * pen0 - e10 * pen5

    # ---------------- (c) per condition
    vals5 = reg5._physical(x)
    lam = {k: float(v.numpy()) for k, v in vals5.items()}
    rows = []
    for c5, c0 in zip(reg5._active, reg0._active):
        assert c5.label == c0.label
        coeff = float(c5.value(vals5, reg5._relu2_tf).numpy())
        p5 = float(c5.penalty(vals5, reg5._relu2_tf).numpy())
        p0 = float(c0.penalty(reg0._physical(x), reg0._relu2_tf).numpy())
        rows.append(
            dict(
                label=c5.label,
                coeff=coeff,
                bound5=c5.bound,
                pen5=p5,
                pen5_scaled_t5=p5 * e10,
                bound0=c0.bound,
                pen0=p0,
                pen0_scaled_t8=p0 * e16,
                active5=p5 > 0,
                active0=p0 > 0,
            )
        )

    out = dict(
        fitresult=FR,
        command=cmd,
        dropped_flags=dropped,
        nll_stored=nll_stored,
        a_L_default_t5_traced=L5_traced,
        a_diff=L5_traced - nll_stored,
        L_default_t5_fresh=L5_t5_fresh,
        fresh_minus_traced=L5_t5_fresh - L5_traced,
        L_base_unwalled=Lbase,
        pen5=pen5,
        pen0=pen0,
        e10=e10,
        e16=e16,
        b_L_margin0_t8=L0_t8,
        b_lhs=lhs,
        b_rhs=rhs,
        b_lhs_minus_rhs=lhs - rhs,
        check_default_eq_base_plus_pen=(L5_traced - (Lbase + e10 * pen5)),
        check_m0_eq_base_plus_pen=(L0_t8 - (Lbase + e16 * pen0)),
        d_traced_after_swap_t8=L_traced_after_swap_t8,
        d_expected_if_reg5_baked=Lbase + e16 * pen5,
        d_expected_if_reg0=L0_t8,
        lambdas_physical=lam,
        held=reg5._held,
        conditions=rows,
        margins=dict(reg5=reg5.margin, reg0=reg0.margin),
        map_keys=dict(reg5=map5.key, reg0=map0.key),
    )
    for k, v in out.items():
        if k not in ("conditions", "command"):
            print(f"[margin_gate] {k} = {v}", flush=True)
    for r in rows:
        print("[c] " + json.dumps(r), flush=True)
    with open(os.path.join(a.outdir, "margin_loss_gate.json"), "w") as fo:
        json.dump(out, fo, indent=1, default=float)
    print("[margin_gate] DONE", flush=True)


if __name__ == "__main__":
    main()
