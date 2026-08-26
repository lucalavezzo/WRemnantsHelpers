#!/usr/bin/env python3
r"""A/B two histmaker outputs: does ``--responseGenBinning`` perturb anything?

The finer response grid is meant to be an ADDITIVE output: the unfolding path
(``nominal_prefsr_yieldsUnfolding``, the ``prefsr``/``prefsr_full`` gen totals and
every other histogram) must come out exactly as before. This checks that claim
histogram by histogram, and it checks it the strict way first:

* every histogram in arm A is present in arm B with the SAME axes (names, sizes,
  edges, flow traits);
* its contents are compared BITWISE (``values``/``variances`` including flow).
  Single-threaded (``-j 1``) runs must be bit-identical. Multi-threaded runs fill
  one shared atomic histogram, so the summation ORDER is not reproducible and the
  right expectation there is float rounding (reported as a relative deviation),
  not bits;
* arm B's extra histograms are listed, and nothing else may be new.

It also runs the internal consistency check that only exists once both grids are
in one file: the response hist coarsened onto the unfolding grid must equal the
unfolding hist summed over the helicity partition -- same events, same weights,
so this is an identity, not an approximation.

Usage:
    ./response_binning_ab.py --a A/mz_dilepton_*.hdf5 --b B/mz_dilepton_*.hdf5
"""

import argparse

import numpy as np


def load_output(path):
    import h5py

    from wums import ioutils as wums_io

    out = {}
    with h5py.File(path, "r") as f:
        for key in f.keys():
            if key in ("meta_info", "meta"):
                continue
            try:
                sample = wums_io.pickle_load_h5py(f[key])
            except Exception as exc:  # noqa: BLE001
                print(f"  [skip] {key}: {exc}")
                continue
            if not isinstance(sample, dict) or "output" not in sample:
                continue
            hists = {}
            for name, proxy in sample["output"].items():
                try:
                    hists[name] = proxy.get() if hasattr(proxy, "get") else proxy
                except Exception as exc:  # noqa: BLE001
                    print(f"  [skip] {key}/{name}: {exc}")
            out[key] = hists
    return out


def axis_sig(h):
    return tuple(
        (
            a.name,
            a.size,
            bool(a.traits.underflow),
            bool(a.traits.overflow),
            tuple(np.round(np.asarray(a.edges, float), 12)) if hasattr(a, "edges") else (),
        )
        for a in h.axes
    )


def arrays(h):
    v = np.asarray(h.values(flow=True), dtype=np.float64)
    try:
        e = np.asarray(h.variances(flow=True), dtype=np.float64)
    except Exception:  # noqa: BLE001
        e = None
    return v, e


def compare(A, B):
    n_same_bits, n_close, n_axis, worst = 0, 0, 0, []
    extra, missing = [], []
    for sample in sorted(set(A) | set(B)):
        ha, hb = A.get(sample, {}), B.get(sample, {})
        for name in sorted(set(ha) | set(hb)):
            if name not in ha:
                extra.append(f"{sample}/{name}")
                continue
            if name not in hb:
                missing.append(f"{sample}/{name}")
                continue
            if axis_sig(ha[name]) != axis_sig(hb[name]):
                n_axis += 1
                print(f"  AXES DIFFER  {sample}/{name}")
                continue
            va, ea = arrays(ha[name])
            vb, eb = arrays(hb[name])
            bits = np.array_equal(va, vb) and (
                ea is None or eb is None or np.array_equal(ea, eb)
            )
            if bits:
                n_same_bits += 1
                continue
            n_close += 1
            den = np.where(np.abs(va) > 0, np.abs(va), np.inf)
            rel = float(np.nanmax(np.abs(vb - va) / den))
            worst.append((rel, f"{sample}/{name}", float(np.nanmax(np.abs(vb - va)))))
    return dict(
        bits=n_same_bits,
        close=n_close,
        axis=n_axis,
        worst=sorted(worst, reverse=True)[:10],
        extra=extra,
        missing=missing,
    )


def coarsen_check(hists, level="prefsr"):
    """response hist coarsened onto the unfolding grid == unfolding hist."""
    jname, rname = f"nominal_{level}_yieldsUnfolding", f"nominal_{level}_yieldsResponse"
    if jname not in hists or rname not in hists:
        print("  (no response hist in this arm -- skipping the identity check)")
        return
    hu = hists[jname]
    hr = hists[rname]
    reco = [a.name for a in hu.axes if a.name in ("ptll", "yll")]
    for acc in (True, False):
        u = hu[{"acceptance": acc}].project(*reco, "ptVGen", "absYVGen")
        r = hr[{"acceptance": acc}].project(*reco, "ptVGen", "absYVGen")
        # merge the response gen axes onto the unfolding ones (flow kept)
        vu = u.values(flow=True)
        vr = r.values(flow=True)
        for ax_name, pos in (("ptVGen", -2), ("absYVGen", -1)):
            eu = np.asarray(u.axes[ax_name].edges, float)
            er = np.asarray(r.axes[ax_name].edges, float)
            # each unfolding edge must be a response edge (nesting)
            idx = [int(np.argmin(np.abs(er - e))) for e in eu]
            assert all(
                abs(er[i] - e) < 1e-9 for i, e in zip(idx, eu)
            ), f"{ax_name}: unfolding edges do not nest in the response edges"
            # in-range groups plus one trailing overflow group
            groups = [(idx[i], idx[i + 1]) for i in range(len(idx) - 1)]
            vr = np.moveaxis(vr, pos, 0)
            uf = 1 if r.axes[ax_name].traits.underflow else 0
            merged = [
                vr[uf + lo : uf + hi].sum(axis=0) for lo, hi in groups
            ]
            if r.axes[ax_name].traits.overflow:
                merged.append(vr[uf + idx[-1] :].sum(axis=0))
            vr = np.moveaxis(np.stack(merged, axis=0), 0, pos)
        num = float(np.abs(vr - vu).max())
        den = float(np.abs(vu).max())
        print(
            f"  acceptance={acc}: max|response(coarsened) - unfolding| = {num:.6g} "
            f"({num / den:.3e} of the largest bin);  sums "
            f"{vr.sum():.10g} vs {vu.sum():.10g} "
            f"(rel {vr.sum() / vu.sum() - 1:+.3e})"
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", required=True, help="baseline histmaker output")
    ap.add_argument("--b", required=True, help="output with --responseGenBinning")
    ap.add_argument("--level", default="prefsr")
    args = ap.parse_args()

    print(f"A = {args.a}\nB = {args.b}\n")
    A = load_output(args.a)
    B = load_output(args.b)
    res = compare(A, B)
    print(
        f"\nhistograms identical BIT FOR BIT : {res['bits']}\n"
        f"histograms differing numerically : {res['close']}\n"
        f"histograms with different axes   : {res['axis']}\n"
        f"only in B (the new outputs)      : {len(res['extra'])}\n"
        f"only in A (LOST -- must be 0)    : {len(res['missing'])}"
    )
    for name in res["extra"]:
        print(f"   + {name}")
    for name in res["missing"]:
        print(f"   - {name}")
    if res["worst"]:
        print("\nlargest relative deviations (float-rounding scale expected):")
        for rel, name, absd in res["worst"]:
            print(f"   {rel:.3e}  (abs {absd:.3e})  {name}")

    print("\ninternal identity check on arm B:")
    for sample, hists in B.items():
        if f"nominal_{args.level}_yieldsResponse" in hists:
            print(f" {sample}:")
            coarsen_check(hists, args.level)


if __name__ == "__main__":
    main()
