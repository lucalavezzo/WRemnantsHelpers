#!/usr/bin/env python3
"""Are two SCETlib autodiff caches the same cache?

Two questions, and they are not the same question:

* ``--bytes A.npz B.npz`` -- structural. Parses both blobs and reports where
  they differ: the header, the per-bin nominal rule, each member's record, the
  frozen fixed-order grid per bin key, each member's fixed-order deltas. This
  is what tells you WHICH member or WHICH field a merge got wrong, instead of
  "the files differ".
* ``--eval --conf runcard --cache A.npz --out a.npz`` -- behavioural. Loads the
  cache through the production loader and dumps value + jacobian at the anchor
  and at a displaced point. Run it once per cache (ONE configure per process --
  a third in the same process segfaults) and then compare with
  ``--diff a.npz b.npz``.

The frozen fixed-order grid is compared PER BIN KEY, never as a byte range:
``_Fo_cache::bins`` is an unordered_map filled by the parallel bin loop, so the
order it is written in is thread scheduling, not content.
"""

import argparse
import importlib.util
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_AD = "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad"


def _bcp():
    spec = importlib.util.spec_from_file_location(
        "bcp", os.path.join(_AD, "build_cache_parallel.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def compare_bytes(pa, pb):
    m = _bcp()
    a, b = np.load(pa, allow_pickle=False), np.load(pb, allow_pickle=False)
    ok = True
    print(f"A {pa}\nB {pb}\n")
    for k in ("format", "n_eig", "has_as", "has_muf", "bins", "anchor", "names"):
        same = np.array_equal(a[k], b[k])
        ok &= same
        print(f"  {k:<8} {'same' if same else 'DIFFER'}")
    ra, rb = (m.parse_rule_blob(x["rules"].tobytes()) for x in (a, b))
    print("\nrule blob:")
    for f in ("version", "sizes", "fingerprint", "opts", "meta"):
        same = ra[f] == rb[f]
        ok &= same
        print(
            f"  {f:<12} {'same' if same else 'DIFFER'}"
            + ("" if same else f"\n     A {ra[f]}\n     B {rb[f]}")
        )
    same = np.array_equal(ra["anchor"], rb["anchor"])
    ok &= same
    print(f"  anchor       {'same' if same else 'DIFFER'}")
    print(f"  bins         {len(ra['rules'])} / {len(rb['rules'])}")
    if len(ra["rules"]) == len(rb["rules"]):
        bad_shared, bad_var, n_var = [], [], set()
        for i, (x, y) in enumerate(zip(ra["rules"], rb["rules"])):
            n_var.add((x["n_var"], y["n_var"]))
            if bytes(ra["buf"][slice(*x["shared"])]) != bytes(
                rb["buf"][slice(*y["shared"])]
            ):
                bad_shared.append(i)
            for j, (va, vb) in enumerate(zip(x["var"], y["var"])):
                if bytes(ra["buf"][slice(*va)]) != bytes(rb["buf"][slice(*vb)]):
                    bad_var.append((i, j))
        print(f"  members/bin  {sorted(n_var)}")
        # Structure vs values: a different SITE COUNT is fatal (Var::w is one
        # weight per site, so a merged rule would read past the end), while
        # equal counts and different numbers is "the same rule, rebuilt to
        # within the integrator tolerance" -- which is still not mergeable, but
        # it is a different failure.
        struct = [
            (
                i,
                x["n_grid"],
                y["n_grid"],
                x["n_sites"],
                y["n_sites"],
                x["n_fo_w"],
                y["n_fo_w"],
            )
            for i, (x, y) in enumerate(zip(ra["rules"], rb["rules"]))
            if (x["n_grid"], x["n_sites"], x["n_fo_w"])
            != (y["n_grid"], y["n_sites"], y["n_fo_w"])
        ]
        print(
            f"  structure (n_grid, n_sites, n_fo_w) differs in {len(struct)} "
            f"bins {struct[:6]}"
        )
        dc = [
            abs(x["c_val"] - y["c_val"]) / max(abs(x["c_val"]), 1e-300)
            for x, y in zip(ra["rules"], rb["rules"])
        ]
        print(f"  rule c_val: max rel difference {max(dc):.3e}")
        print(
            f"  nominal rule differs in {len(bad_shared)} of "
            f"{len(ra['rules'])} bins" + (f" {bad_shared[:10]}" if bad_shared else "")
        )
        print(
            f"  member data differs in {len(bad_var)} (bin, member) records"
            + (f" {bad_var[:10]}" if bad_var else "")
        )
        ok &= not bad_shared and not bad_var
    fa, fb = (m.parse_fo_blob(x["fo"].tobytes()) for x in (a, b))
    print("\nfixed-order blob:")
    for f in ("version", "fingerprint", "meta"):
        same = fa[f] == fb[f]
        ok &= same
        print(
            f"  {f:<12} {'same' if same else 'DIFFER'}"
            + ("" if same else f"\n     A {fa[f]}\n     B {fb[f]}")
        )
    same = set(fa["grid"]) == set(fb["grid"])
    ok &= same
    print(
        f"  grid keys    {'same' if same else 'DIFFER'} "
        f"({len(fa['grid'])} / {len(fb['grid'])})"
    )
    if same:
        bad = [k for k in fa["grid"] if fa["grid"][k] != fb["grid"][k]]
        ok &= not bad
        print(f"  frozen grid differs in {len(bad)} of {len(fa['grid'])} bins")
        same_order = list(fa["grid"]) == list(fb["grid"])
        note = (
            "identical"
            if same_order
            else "differs -- unordered_map, not a content difference"
        )
        print(f"  (write order {note})")
    print(f"  deltas       {len(fa['deltas'])} / {len(fb['deltas'])}")
    if len(fa["deltas"]) == len(fb["deltas"]):
        bad = [i for i, (x, y) in enumerate(zip(fa["deltas"], fb["deltas"])) if x != y]
        ok &= not bad
        print(f"  member deltas differ for {len(bad)} members {bad[:10]}")
    for i in range(2):
        ga, gb = fa["muf"][i], fb["muf"][i]
        if (ga is None) != (gb is None):
            ok = False
            print(f"  muF grid {i}: present in only one")
        elif ga is not None:
            bad = set(ga) != set(gb) or any(ga[k] != gb[k] for k in ga)
            ok &= not bad
            print(f"  muF grid {i}: {'DIFFERS' if bad else 'same'} ({len(ga)} bins)")
    same = np.array_equal(fa["var_bins"], fb["var_bins"])
    ok &= same
    print(f"  var_bins     {'same' if same else 'DIFFER'}")
    print(f"\n=> the two caches are {'IDENTICAL' if ok else 'DIFFERENT'}")
    return 0 if ok else 1


def evaluate(conf, cache, out, scale):
    sys.path.insert(0, os.path.dirname(os.path.dirname(_AD)))
    sys.path.insert(0, "/home/submit/lavezzo/alphaS/WRemnants")
    from wremnants.postprocessing.scetlib_ad.xsec_backend import ScetlibADXsec

    core = ScetlibADXsec(conf, cache, threads=8)
    p0 = core.anchor.copy()
    v0, j0 = (np.array(x) for x in core.values_and_jacobian(p0))
    # A displaced point, because the rules are LOCAL to the anchor: agreeing at
    # the anchor alone would not test the member interpolation, whose weights
    # are 0.5*(t^2 +- t) and so vanish at t = 0 for the alphaS and muF pairs.
    rng = np.random.default_rng(20260825)
    step = np.where(np.abs(p0) > 0, np.abs(p0), 1.0) * scale
    p1 = p0 + step * rng.uniform(-1.0, 1.0, p0.size)
    v1, j1 = (np.array(x) for x in core.values_and_jacobian(p1))
    np.savez(
        out,
        p0=p0,
        v0=v0,
        j0=j0,
        p1=p1,
        v1=v1,
        j1=j1,
        names=np.array(core.param_names),
        bins=core.bins,
    )
    print(
        f"wrote {out}: {core.n_bins} bins, {core.n_params} params, "
        f"sum(sigma) anchor {v0.sum():.10g} displaced {v1.sum():.10g}"
    )


def diff_eval(pa, pb):
    a, b = np.load(pa, allow_pickle=False), np.load(pb, allow_pickle=False)
    if not np.array_equal(a["names"], b["names"]):
        raise SystemExit("different parameter sets")
    if not np.array_equal(a["p1"], b["p1"]):
        raise SystemExit("different displaced points -- rerun with the same seed")
    # Bins are matched by VALUE and only the common ones are compared, so a
    # cache merged over bin subsets can be diffed against one of its parts:
    # every bin's rule is self-contained, so those rows must come out
    # bit-identical, subset or not.
    ka = [row.tobytes() for row in np.ascontiguousarray(a["bins"], dtype="<f8")]
    kb = [row.tobytes() for row in np.ascontiguousarray(b["bins"], dtype="<f8")]
    common = [k for k in ka if k in set(kb)]
    ia = [ka.index(k) for k in common]
    ib = [kb.index(k) for k in common]
    if len(common) != len(ka) or len(common) != len(kb):
        print(
            f"  comparing the {len(common)} bins in common "
            f"(A has {len(ka)}, B has {len(kb)})"
        )
    worst = 0.0
    for tag in ("0", "1"):
        for what in ("v", "j"):
            x, y = a[what + tag][ia], b[what + tag][ib]
            d = np.abs(x - y)
            # Normalised by the array's own scale, not element by element: a
            # Jacobian entry that is ~0 would otherwise report a huge relative
            # difference for an utterly negligible absolute one.
            scale = max(float(np.abs(x).max()), float(np.abs(y).max()), 1e-300)
            r = float(d.max() / scale) if x.size else 0.0
            worst = max(worst, r)
            print(
                f"  {'anchor' if tag == '0' else 'displaced'} "
                f"{'value' if what == 'v' else 'jacobian'}: max |A-B| "
                f"{d.max():.3e}, max/scale {r:.3e}, bit-identical "
                f"{np.array_equal(x, y)}"
            )
    print(
        f"\nworst relative difference {worst:.3e} -> "
        f"{'PASS' if worst < 1e-12 else 'FAIL'}"
    )
    return 0 if worst < 1e-12 else 1


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--bytes", nargs=2, metavar=("A.npz", "B.npz"))
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--conf")
    ap.add_argument("--cache")
    ap.add_argument("--out")
    ap.add_argument(
        "--scale",
        type=float,
        default=0.1,
        help="size of the displacement, relative to each parameter",
    )
    ap.add_argument("--diff", nargs=2, metavar=("a.npz", "b.npz"))
    args = ap.parse_args()
    rc = 0
    if args.bytes:
        rc |= compare_bytes(*args.bytes)
    if args.eval:
        evaluate(args.conf, args.cache, args.out, args.scale)
    if args.diff:
        rc |= diff_eval(*args.diff)
    sys.exit(rc)


if __name__ == "__main__":
    main()
