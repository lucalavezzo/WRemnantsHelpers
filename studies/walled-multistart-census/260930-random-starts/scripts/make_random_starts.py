#!/usr/bin/env python3
"""Randomised, physically-feasible --externalPostfit seeds around a reference minimum.

    make_random_starts.py --ref <fitresults.hdf5> --n N --seed S --out <dir> [knobs]

Writes N seed files ``<out>/<prefix>_<k>.hdf5`` in exactly the format rabbit's
``--externalPostfit`` reads (``Fitter.load_fitresult``, flat route: a top-level ``x``
dataset + ``parms`` names), written with rabbit's OWN writer
``rabbit.snapshot.write_snapshot`` -- the same writer the fit's periodic
``snapshot_fitresults_*.hdf5`` files come from -- plus ``<out>/manifest.csv``.

COORDINATES. Everything is done in the stored x coordinates of the reference, i.e. the
raw ``Fitter.x`` vector: the fitresult's ``parms`` histogram values ARE that vector
(``ws.add_parms_hist(values=ifitter.x)``), and so is a snapshot's ``x``. For a blinded
fit that vector is in the BLINDED frame for ``alphaS`` (the additive offset is applied
inside ``get_poi``, never to x). load_fitresult assigns these values raw into x, so a
seed written here lands exactly where it says, in the same frame the fit minimises in.
Nothing here arms, disarms or reads a blinding offset.

DRAW RULES (--mode perturb, the default)
  * non-NP parameters (all but alphaS and the fitted NP lambdas):
        x = x_ref + s * L z,   z ~ N(0, 1),   L = chol(postfit cov restricted to that block)
  * fitted NP lambdas (those in the param model's parameter list AND present in parms;
    held ones -- lambda_inf, lambda_inf_nu, and lambda4_nu when it is not fitted -- are
    left alone): each lambda uniform over the PHYSICAL box (--range), mapped back to
    theta with the wall's own ``physical_spec`` (physical = anchor + width*theta, anchor
    from the card's recorded correction runcard). The joint draw is REJECTED and redrawn
    until every ``damping_conditions`` Condition holds (value >= bound) at --margin
    (default 0), evaluated with the wall's own Condition objects and ``numpy_relu2`` at
    |Y| = 0 and at the card's binding |Y| (``_binding_absY`` on the card).
  * alphaS: x = x_ref + u * sigma_ref, u ~ U[-A, A] (A = --alphas-u, default 2).
    Only u is logged.

--mode cold_except_alphas
  every parameter at rabbit's cold start (x0default, assigned raw by
  ``Fitter.xdefaultassign``; the reference's ``parms_prefit`` histogram IS that vector,
  written right after ``defaultassign()`` and before ``--externalPostfit`` is loaded),
  except alphaS = x_ref (blinded). With --cold-alphas-u A > 0 alphaS is instead
  x_ref + u*sigma_ref, u ~ U[-A, A] (default 0: exactly x_ref, so one file is written).

BLINDING. No absolute alphaS is computed, printed or saved. The seed files hold the
BLINDED alphaS x, as every fitresult/snapshot of a blinded fit already does. The
manifest and stdout carry only u.
"""

import argparse
import csv
import os
import shlex
import sys

import h5py
import numpy as np

RABBIT_BIN = os.path.join(
    os.environ.get("WREM_BASE", "/home/submit/lavezzo/alphaS/WRemnants"),
    "rabbit",
    "bin",
)

DEFAULT_RANGES = {
    "lambda2": (0.0, 0.5),
    "delta_lambda2": (-0.03, 0.01),
    "lambda4": (0.0, 0.3),
    "lambda2_nu": (0.0, 0.3),
    "lambda4_nu": (0.0, 0.1),
}
NEAR_ACTIVE = 1e-3  # a face counts as "near-active" when value - bound < this


# --------------------------------------------------------------------------------------
# reference + wall inputs
# --------------------------------------------------------------------------------------


def load_reference(path, poi="alphaS"):
    from rabbit import io_tools

    fr, meta = io_tools.get_fitresult(path, meta=True)
    h = fr["parms"].get()
    names = np.array(h.axes["parms"]).astype(str)
    x_ref = np.asarray(h.values(), dtype=np.float64).copy()
    hp = fr["parms_prefit"].get()
    names_p = np.array(hp.axes["parms"]).astype(str)
    if not np.array_equal(names, names_p):
        raise RuntimeError("parms and parms_prefit axes differ in the reference")
    x0 = np.asarray(hp.values(), dtype=np.float64).copy()
    cov = np.asarray(fr["cov"].get().values(), dtype=np.float64)
    if cov.shape != (len(names), len(names)):
        raise RuntimeError(f"cov shape {cov.shape} vs {len(names)} parms")
    pois = [
        p.decode() if isinstance(p, bytes) else str(p) for p in meta.get("pois", [])
    ]
    if poi not in names:
        raise RuntimeError(f"{poi} not in the reference parms")
    return dict(
        path=path, names=names, x_ref=x_ref, x0=x0, cov=cov, meta=meta, pois=pois
    )


def reference_command_args(meta):
    """The reference fit's own rabbit_fit argv, parsed with rabbit's own parser."""
    if RABBIT_BIN not in sys.path:
        sys.path.insert(0, RABBIT_BIN)
    import rabbit_fit

    cmd = meta["meta_info"]["command"]
    argv = shlex.split(cmd)[1:]
    return rabbit_fit.make_parser().parse_args(argv), cmd


def wall_inputs(ref, ymax=None):
    """Forms, specs, anchors and binding |Y|, via the WALL's own resolver on the card.

    Also cross-checks the anchors against the fitresult's meta chain, the route
    studies/alphas-scan-discontinuity/260925-y35zwarm-np-impacts/scripts/physical_lambdas.py
    uses, and refuses on any disagreement.
    """
    from rabbit import inputdata

    from wremnants.postprocessing.scetlib_ad import np_damping_wall as W
    from wremnants.postprocessing.scetlib_ad import params as P
    from wremnants.postprocessing.scetlib_ad import response as R

    fargs, cmd = reference_command_args(ref["meta"])

    # a ymax= on the reference's own -r line wins over the card, exactly as in the fit
    r_ymax = None
    for margs in fargs.regularization:
        if margs and margs[0].endswith("NPDampingWall"):
            for a in margs[2:]:
                if a.startswith("ymax="):
                    r_ymax = float(a.split("=", 1)[1])
    indata = inputdata.FitInputData(fargs.filename, None, host_memory=True)
    use_ymax = ymax if ymax is not None else r_ymax
    wi = W.resolve_wall_inputs(indata, ymax=use_ymax)

    # cross-check vs the fitresult meta chain (physical_lambdas.py route)
    entry = R.corr_config_from_meta(ref["meta"])
    if entry is None:
        raise RuntimeError("no scetlib_corr_config in the fitresult meta chain")
    cfg = entry["config"]
    forms = W.forms_from_corr_config(cfg)
    if forms != (wi["np_model"], wi["np_model_nu"]):
        raise RuntimeError(f"forms differ: meta {forms} vs card {wi['np_model']}")
    for n in wi["names"]:
        a_meta = P.corr_anchor_value(cfg, n)
        if a_meta != wi["anchors"][n] or W.physical_spec(cfg, n) != wi["specs"][n]:
            raise RuntimeError(
                f"{n}: card and fitresult meta disagree on anchor/spec "
                f"({wi['anchors'][n]}, {wi['specs'][n]}) vs ({a_meta}, "
                f"{W.physical_spec(cfg, n)})"
            )

    fit_params = None
    pm_args = [a for pm in (fargs.paramModel or []) for a in pm[1:]]
    for a in pm_args:
        if a.startswith("fit_params="):
            fit_params = a.split("=", 1)[1].split(",")
    wi.update(
        card=fargs.filename,
        ref_margin_line=[m for m in fargs.regularization],
        fit_params=fit_params,
        ymax_used=wi["ymax"],
    )
    return wi


# --------------------------------------------------------------------------------------
# NP draw with rejection on the wall's own conditions
# --------------------------------------------------------------------------------------


class NPSampler:
    def __init__(self, wi, names, ranges, margin):
        from wremnants.postprocessing.scetlib_ad import np_damping_wall as W

        self.W = W
        self.wi = wi
        self.margin = W._parse_margin(margin)
        self.conds = W.damping_conditions(
            wi["np_model"], wi["np_model_nu"], wi["ymax"], margin=self.margin
        )
        names = list(names)
        self.fitted = [n for n in wi["names"] if n in names]
        self.held = {n: float(wi["anchors"][n]) for n in wi["names"] if n not in names}
        for n, a in self.held.items():
            if a is None:
                raise RuntimeError(f"held lambda {n} has no anchor")
        if wi["fit_params"] is not None:
            extra = [n for n in self.fitted if n not in wi["fit_params"]]
            if extra:
                raise RuntimeError(
                    f"{extra} in parms but not in the param model's fit_params"
                )
        self.idx = {n: names.index(n) for n in self.fitted}
        self.ranges = {}
        for n in self.fitted:
            if n not in ranges:
                raise RuntimeError(f"no --range for fitted lambda {n}")
            kind, coeffs = wi["specs"][n]
            if kind != "quad" or coeffs[2] != 0.0:
                raise RuntimeError(
                    f"{n}: spec {wi['specs'][n]} is not linear; inverse map undefined"
                )
            self.ranges[n] = ranges[n]

    def theta_of(self, n, phys):
        c0, c1, _ = self.wi["specs"][n][1]
        return (phys - c0) / c1

    def phys_of(self, n, theta):
        return float(self.W.physical_from_theta(self.wi["specs"][n], theta))

    def values(self, phys):
        v = dict(self.held)
        v.update(phys)
        return v

    def evaluate(self, phys):
        """[(label, value, bound, active)] of every condition at these physical lambdas.

        ``active`` mirrors NPDampingWall.set_expectations: a condition reading at least
        one FITTED lambda is armed (enforced at its bound, i.e. the margin); one reading
        only HELD lambdas is dropped from the loss and checked once against the BARE
        condition (value >= 0) -- e.g. lambda4_nu >= 0 with lambda4_nu held at 0.
        """
        v = self.values(phys)
        out = []
        for c in self.conds:
            val = np.atleast_1d(np.asarray(c.value(v, self.W.numpy_relu2), dtype=float))
            active = any(n in self.idx for n in c.names)
            bound = float(c.bound) if active else 0.0
            out.append((c.label, float(np.min(val)), bound, active))
        return out

    def feasible(self, phys):
        return all(val >= b for _, val, b, _ in self.evaluate(phys))

    def near_active(self, phys, tol=NEAR_ACTIVE):
        """Armed faces (fitted-lambda conditions) with value - bound < tol."""
        return [
            lab for lab, val, b, act in self.evaluate(phys) if act and val - b < tol
        ]

    def draw(self, rng, max_tries=1_000_000):
        for k in range(1, max_tries + 1):
            phys = {n: float(rng.uniform(*self.ranges[n])) for n in self.fitted}
            if self.feasible(phys):
                return phys, k
        raise RuntimeError(f"no feasible NP draw in {max_tries} tries")


# --------------------------------------------------------------------------------------
# writing + round trip
# --------------------------------------------------------------------------------------


def read_like_load_fitresult(path):
    """Exactly the flat branch of rabbit Fitter.load_fitresult."""
    with h5py.File(path, "r") as fext:
        assert "x" in fext.keys(), "not a flat seed file"
        x_ext = fext["x"][...]
        parms_ext = fext["parms"][...].astype(str)
        has_cov = "cov" in fext.keys()
    return x_ext, parms_ext, has_cov


def write_seed(path, names, x, attrs):
    from rabbit import snapshot

    snapshot.write_snapshot(path, names, x, meta=attrs)
    x_back, names_back, has_cov = read_like_load_fitresult(path)
    ok = (
        x_back.dtype == np.float64
        and x_back.shape == x.shape
        and np.array_equal(x_back.view(np.uint64), x.view(np.uint64))
        and np.array_equal(names_back, names)
        and not has_cov
    )
    if not ok:
        raise RuntimeError(f"round trip FAILED for {path}")
    return True


def parse_ranges(items):
    ranges = dict(DEFAULT_RANGES)
    for it in items or []:
        name, rng = it.split("=", 1)
        lo, hi = (float(t) for t in rng.split(","))
        if not hi > lo:
            raise ValueError(f"--range {it}: need hi > lo")
        ranges[name] = (lo, hi)
    return ranges


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--ref", required=True, help="reference fitresults.hdf5")
    ap.add_argument("--n", type=int, default=10, help="number of seeds")
    ap.add_argument("--seed", type=int, default=0, help="master RNG seed")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--prefix", default="seed")
    ap.add_argument(
        "--mode", choices=("perturb", "cold_except_alphas"), default="perturb"
    )
    ap.add_argument("--s", type=float, default=2.0, help="non-NP scale s (x Cholesky)")
    ap.add_argument(
        "--alphas-u", type=float, default=2.0, help="alphaS u ~ U[-A, A] (perturb)"
    )
    ap.add_argument(
        "--cold-alphas-u",
        type=float,
        default=0.0,
        help="cold_except_alphas: u ~ U[-A,A]; 0 => alphaS exactly x_ref (1 file)",
    )
    ap.add_argument(
        "--range",
        action="append",
        metavar="NAME=LO,HI",
        help=f"physical box per NP lambda; defaults {DEFAULT_RANGES}",
    )
    ap.add_argument(
        "--margin", type=float, default=0.0, help="wall margin for rejection"
    )
    ap.add_argument(
        "--ymax", type=float, default=None, help="override binding |Y| (default: card)"
    )
    ap.add_argument("--poi", default="alphaS", help="the blinded parameter")
    ap.add_argument(
        "--no-np-draw",
        action="store_true",
        help="perturb mode: keep NP lambdas at x_ref (debug)",
    )
    ap.add_argument(
        "--plot-sample",
        type=int,
        default=0,
        help="also draw this many NP points (same rules, not written) for the figure",
    )
    ap.add_argument(
        "--plot-dir", default=None, help="where save_plot writes the figure"
    )
    ap.add_argument("--plot-name", default="np_lambda_draws")
    args = ap.parse_args()

    ref = load_reference(args.ref, poi=args.poi)
    names, x_ref, x0, cov = ref["names"], ref["x_ref"], ref["x0"], ref["cov"]
    wi = wall_inputs(ref, ymax=args.ymax)
    ranges = parse_ranges(args.range)
    sampler = NPSampler(wi, names, ranges, args.margin)

    ia = int(np.where(names == args.poi)[0][0])
    sig_a = float(np.sqrt(cov[ia, ia]))
    np_idx = np.array([sampler.idx[n] for n in sampler.fitted], dtype=int)
    mask_non = np.ones(len(names), dtype=bool)
    mask_non[np_idx] = False
    mask_non[ia] = False
    idx_non = np.where(mask_non)[0]

    print(f"[ref] {args.ref}")
    print(f"[ref] {len(names)} parms; POI {args.poi} (blinded x; only u is reported)")
    print(f"[ref] card {wi['card']}")
    print(
        f"[wall] forms np_model={wi['np_model']} np_model_nu={wi['np_model_nu']}  "
        f"binding |Y| = {wi['ymax']:g} from {wi['ymax_source']}  margin={sampler.margin:g}"
    )
    print(
        f"[wall] {len(sampler.conds)} conditions; fitted {sampler.fitted}; held {sampler.held}"
    )
    for lab, val, b, act in sampler.evaluate(
        {n: sampler.phys_of(n, x_ref[sampler.idx[n]]) for n in sampler.fitted}
    ):
        print(
            f"[wall]   {'armed ' if act else 'held  '} {lab:62s} bound {b:g}  (at ref: value-bound {val - b:+.4g})"
        )
    for n in sampler.fitted:
        c0, c1, _ = wi["specs"][n][1]
        print(
            f"[np] {n:14s} physical = {c0:g} + {c1:g}*theta ; box {ranges[n]} -> theta "
            f"[{sampler.theta_of(n, ranges[n][0]):+.4f}, {sampler.theta_of(n, ranges[n][1]):+.4f}]"
            f" ; ref phys {sampler.phys_of(n, x_ref[sampler.idx[n]]):.5f}"
        )

    ss = np.random.SeedSequence(args.seed)
    L = None
    if args.mode == "perturb":
        C = cov[np.ix_(idx_non, idx_non)]
        L = np.linalg.cholesky(C)  # raises if not PD
        sig_non = np.sqrt(np.diag(C))
        print(f"[cov] non-NP block {len(idx_non)}x{len(idx_non)} Cholesky OK")

    n_files = args.n
    if args.mode == "cold_except_alphas" and args.cold_alphas_u == 0.0:
        if args.n != 1:
            print(
                "[cold] --cold-alphas-u 0: every seed would be identical; writing 1 file"
            )
        n_files = 1

    os.makedirs(args.out, exist_ok=True)
    rows = []
    children = ss.spawn(n_files)
    for k in range(n_files):
        rng = np.random.default_rng(children[k])
        path = os.path.join(args.out, f"{args.prefix}_{k:03d}.hdf5")
        row = dict(seed_id=k, file=os.path.basename(path), mode=args.mode)
        if args.mode == "perturb":
            x = x_ref.copy()
            z = rng.standard_normal(len(idx_non))
            dx = args.s * (L @ z)
            x[idx_non] = x_ref[idx_non] + dx
            u = float(rng.uniform(-args.alphas_u, args.alphas_u))
            x[ia] = x_ref[ia] + u * sig_a
            if args.no_np_draw:
                phys = {
                    n: sampler.phys_of(n, x_ref[sampler.idx[n]]) for n in sampler.fitted
                }
                ntry = 0
            else:
                phys, ntry = sampler.draw(rng)
                for n, p in phys.items():
                    x[sampler.idx[n]] = sampler.theta_of(n, p)
            row.update(
                u=u,
                max_abs_z=float(np.max(np.abs(z))),
                max_abs_pull_nonnp=float(np.max(np.abs(dx) / sig_non)),
                chi2_z=float(z @ z),
                n_tries=ntry,
            )
        else:
            x = x0.copy()
            u = (
                float(rng.uniform(-args.cold_alphas_u, args.cold_alphas_u))
                if args.cold_alphas_u > 0
                else 0.0
            )
            x[ia] = x_ref[ia] + u * sig_a
            phys = {n: sampler.phys_of(n, x[sampler.idx[n]]) for n in sampler.fitted}
            row.update(
                u=u,
                max_abs_z=float("nan"),
                max_abs_pull_nonnp=float("nan"),
                chi2_z=float("nan"),
                n_tries=0,
            )
        # the physical lambdas as the WRITTEN theta maps them (not the drawn floats)
        phys_w = {n: sampler.phys_of(n, x[sampler.idx[n]]) for n in sampler.fitted}
        feas = sampler.feasible(phys_w)
        row.update({n: phys_w[n] for n in sampler.fitted})
        row["feasible_margin"] = feas
        row["near_active_faces"] = ";".join(sampler.near_active(phys_w)) or "-"
        attrs = dict(
            reference=args.ref,
            mode=args.mode,
            seed_id=k,
            master_seed=args.seed,
            s=args.s,
            u=u,
            margin=sampler.margin,
            ymax=wi["ymax"],
            writer="make_random_starts.py (rabbit.snapshot.write_snapshot)",
        )
        write_seed(path, names, x, attrs)
        row["roundtrip"] = True
        rows.append(row)
        print(
            f"[seed {k:03d}] u={u:+.3f} "
            + " ".join(f"{n}={phys_w[n]:.4f}" for n in sampler.fitted)
            + f" feasible={feas} near-active={row['near_active_faces']}"
            + (
                f" max|z|={row['max_abs_z']:.2f} tries={row['n_tries']}"
                if args.mode == "perturb"
                else ""
            )
        )

    cols = (
        ["seed_id", "file", "mode", "u"]
        + sampler.fitted
        + [
            "max_abs_z",
            "max_abs_pull_nonnp",
            "chi2_z",
            "n_tries",
            "feasible_margin",
            "near_active_faces",
            "roundtrip",
        ]
    )
    man = os.path.join(args.out, f"manifest_{args.prefix}.csv")
    with open(man, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"[out] {n_files} seeds + {man}")
    if not all(r["feasible_margin"] for r in rows):
        print("[WARN] some written seeds are NOT feasible at the margin (cold start?)")

    if args.plot_sample > 0 or args.plot_dir:
        sample = []
        if args.plot_sample > 0:
            prng = np.random.default_rng(ss.spawn(1)[0])
            ntot = 0
            for _ in range(args.plot_sample):
                p, t = sampler.draw(prng)
                sample.append(p)
                ntot += t
            print(
                f"[plot] acceptance {args.plot_sample / ntot:.3f} over {ntot} raw draws"
            )
        ref_phys = {
            n: sampler.phys_of(n, x_ref[sampler.idx[n]]) for n in sampler.fitted
        }
        make_plot(args, sampler, ranges, sample, rows, ref_phys)


def make_plot(args, sampler, ranges, sample, rows, ref_phys):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from plot_output import save_plot

    lab = {
        "lambda2": r"$\lambda_2$",
        "delta_lambda2": r"$\delta\lambda_2$",
        "lambda4": r"$\lambda_4$",
        "lambda2_nu": r"$\lambda_2^\nu$",
        "lambda4_nu": r"$\lambda_4^\nu$",
    }
    ns = sampler.fitted
    m = len(ns)
    fig, axs = plt.subplots(m, m, figsize=(2.6 * m, 2.6 * m))
    S = {n: np.array([p[n] for p in sample]) for n in ns} if sample else None
    D = {n: np.array([r[n] for r in rows]) for n in ns}
    for i, ni in enumerate(ns):
        for j, nj in enumerate(ns):
            ax = axs[i, j]
            if j > i:
                ax.axis("off")
                continue
            if i == j:
                if S is not None:
                    ax.hist(
                        S[ni], bins=30, range=ranges[ni], color="0.75", density=True
                    )
                for v in D[ni]:
                    ax.axvline(v, color="C0", lw=0.8)
                ax.axvline(ref_phys[ni], color="C3", lw=1.5, ls="--")
                ax.set_yticks([])
            else:
                if S is not None:
                    ax.scatter(S[nj], S[ni], s=2, color="0.7", rasterized=True)
                ax.scatter(D[nj], D[ni], s=18, color="C0", zorder=3)
                ax.scatter(
                    [ref_phys[nj]],
                    [ref_phys[ni]],
                    marker="*",
                    s=90,
                    color="C3",
                    zorder=4,
                )
                ax.set_ylim(*ranges[ni])
                if {ni, nj} == {"lambda2", "delta_lambda2"}:
                    y2 = sampler.wi["ymax"] ** 2
                    l2 = np.linspace(*ranges["lambda2"], 50)
                    dl = -l2 / y2
                    if nj == "lambda2":
                        ax.plot(l2, dl, "k-", lw=1)
                    else:
                        ax.plot(dl, l2, "k-", lw=1)
            ax.set_xlim(*ranges[nj])
            if i == m - 1:
                ax.set_xlabel(lab.get(nj, nj))
            else:
                ax.set_xticklabels([])
            if j == 0 and i != 0:
                ax.set_ylabel(lab.get(ni, ni))
            elif j != 0:
                ax.set_yticklabels([])
    fig.suptitle(
        f"NP start draws (physical units): grey = {len(sample)} accepted draws, "
        f"blue = the {len(rows)} written seeds, red = reference minimum\n"
        f"uniform box, rejected unless every NPDampingWall condition holds at margin "
        f"{sampler.margin:g}, |Y| = 0 and {sampler.wi['ymax']:g} (black: L2(|Y|max) = 0)",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_plot(
        outdir=args.plot_dir or args.out,
        basename=args.plot_name,
        fig=fig,
        args=args,
        meta_info={"reference": args.ref, "ymax": sampler.wi["ymax"]},
    )
    print(f"[plot] {args.plot_dir or args.out}/{args.plot_name}.png")


if __name__ == "__main__":
    main()
