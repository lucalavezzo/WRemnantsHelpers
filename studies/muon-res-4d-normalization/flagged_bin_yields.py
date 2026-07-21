#!/usr/bin/env python3
"""Print the event yield in the bins that rabbit_debug_inputdata.py flags for
large systematic variations.

For a rabbit datacard (ZMassDilepton.hdf5), find every bin where some
systematic moves the given process by more than a threshold factor
(default 2x up or 0.5x down, matching rabbit_debug_inputdata's criterion of
|logk| > log(threshold)), and print that bin's yield: nominal sumw, the MC stat
error sqrt(sumw2), the effective event count n_eff = sumw^2/sumw2, the worst
|logk| and which systematic produced it.

The point of the tool: these flagged bins are near-empty cancellation residuals
(n_eff << 1), so their nominal sits far below its own stat error and any
log-normal syst ratio there is floating-point noise. See
studies/muon-res-4d-normalization/LOGBOOK.md.

Runs on the login node (h5py only, no TensorFlow / no container needed).

Usage:
    python3 flagged_bin_yields.py CARD.hdf5 [--process Ztautau] [--threshold 2.0]
                                            [--top 20] [--channel ch0]

Examples:
    python3 flagged_bin_yields.py \\
        /scratch/submit/cms/areimers/alphas/fitinput/AlphaS/Theorymodels/\\
ZMassDilepton_..._Ptll0to44/ZMassDilepton.hdf5
    python3 flagged_bin_yields.py CARD.hdf5 --process Other --threshold 10 --top 40
"""

import argparse
import pickle
import re

import hdf5plugin  # noqa: F401  (registers the blosc filter used by the cards)
import h5py
import numpy as np


def syst_family(name):
    """Collapse a systematic name to its family (strip trailing var index)."""
    if name.startswith("Resolution_correction_smearing"):
        return "Resolution_smearing"
    if name.startswith("Scale_correction"):
        return "Scale_correction"
    n = re.sub(r"\d+$", "", name)
    n = re.sub(r"(SymAvg|SymDiff)$", "", n)
    return n.rstrip("_") or name


def build_channel_map(meta):
    """Return list of (name, axis_names, axis_edges, sizes, offset) per channel,
    in the flat-bin order used by hnorm/hsumw (channels concatenated)."""
    chans = []
    offset = 0
    for name, info in meta["channel_info"].items():
        if info.get("masked", False):
            # masked channels are not in the (unmasked) hnorm/hdata layout
            continue
        axes = info["axes"]
        sizes = [a.size for a in axes]
        anames = [getattr(a, "name", f"ax{i}") for i, a in enumerate(axes)]
        edges = [np.asarray(a.edges) for a in axes]
        n = int(np.prod(sizes)) if sizes else 1
        chans.append(
            dict(name=name, anames=anames, edges=edges, sizes=sizes, offset=offset, n=n)
        )
        offset += n
    return chans


def locate(chans, B):
    """Map a global flat bin index B to (channel, list-of-(axname, lo, hi))."""
    for c in chans:
        if c["offset"] <= B < c["offset"] + c["n"]:
            idx = np.unravel_index(B - c["offset"], c["sizes"])
            coords = []
            for k, i in enumerate(idx):
                e = c["edges"][k]
                # quantile/index axes have integer-ish edges; show the bin index
                lo, hi = e[i], e[i + 1]
                coords.append((c["anames"][k], lo, hi, int(i)))
            return c["name"], coords
    return "?", []


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("card", help="path to ZMassDilepton.hdf5 rabbit datacard")
    p.add_argument(
        "--process", default="Ztautau", help="process to inspect (default: Ztautau)"
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="flag a bin if any syst gives up>threshold or "
        "down<1/threshold, i.e. |logk|>log(threshold) "
        "(default 2.0, matches rabbit_debug_inputdata)",
    )
    p.add_argument(
        "--top",
        type=int,
        default=20,
        help="show this many worst bins (0 = all). Default 20.",
    )
    p.add_argument(
        "--by-syst",
        action="store_true",
        help="also cross-tabulate: do different systematics trip the "
        "SAME bins or different ones? (per-bin syst count, "
        "per-syst bin count, per-family rollup)",
    )
    args = p.parse_args()

    log_thr = np.log(args.threshold)

    with h5py.File(args.card, "r") as f:
        procs = [x.decode() if isinstance(x, bytes) else x for x in f["hprocs"][:]]
        if args.process not in procs:
            raise SystemExit(f"process {args.process!r} not in card procs {procs}")
        ip = procs.index(args.process)
        NPROC = len(procs)
        systs = [x.decode() if isinstance(x, bytes) else x for x in f["hsysts"][:]]
        NS = len(systs)
        nb = int(f["hnorm"].attrs["original_shape"][0])

        sumw = f["hsumw"][:].reshape(nb, NPROC)[:, ip]
        sumw2 = f["hsumw2"][:].reshape(nb, NPROC)[:, ip]

        meta = pickle.loads(f["meta/pickle_data"][:].tobytes())
        chans = build_channel_map(meta)

        # Stream hlogk; for this process compute per-bin max|logk| and which syst.
        # Also accumulate, per syst and per bin, how many (bin,syst) cells trip
        # the flag (|logk|>log_thr) -> answers "same bins or different?".
        ds = f["hlogk"]
        maxlogk = np.zeros(nb)  # per bin: largest |logk| over systs
        argsyst = np.zeros(nb, dtype=np.int64)
        maxlogk_syst = np.zeros(NS)  # per syst: largest |logk| over bins
        argbin_syst = np.zeros(NS, dtype=np.int64)
        trips_per_syst = np.zeros(NS, dtype=np.int64)
        trips_per_bin = np.zeros(nb, dtype=np.int64)
        rows_per_chunk = max(1, 40_000_000 // NS)
        nrow = nb * NPROC
        for r0 in range(0, nrow, rows_per_chunk * NPROC):
            r1 = min(r0 + rows_per_chunk * NPROC, nrow)
            block = ds[r0 * NS : r1 * NS].reshape((r1 - r0) // NPROC, NPROC, NS)
            proc_block = np.abs(block[:, ip, :])
            b0 = r0 // NPROC
            b1 = r1 // NPROC
            maxlogk[b0:b1] = proc_block.max(axis=1)
            argsyst[b0:b1] = proc_block.argmax(axis=1)
            # per-syst largest variation (and which bin) across this chunk
            chunk_syst_max = proc_block.max(axis=0)
            chunk_syst_arg = proc_block.argmax(axis=0) + b0
            upd = chunk_syst_max > maxlogk_syst
            maxlogk_syst[upd] = chunk_syst_max[upd]
            argbin_syst[upd] = chunk_syst_arg[upd]
            trip = proc_block > log_thr
            trips_per_syst += trip.sum(axis=0)
            trips_per_bin[b0:b1] = trip.sum(axis=1)

    ok = (sumw > 0) & (sumw2 > 0)
    neff = np.full(nb, np.inf)
    neff[ok] = sumw[ok] ** 2 / sumw2[ok]

    flagged = np.where((maxlogk > log_thr) & (sumw > 0))[0]
    flagged = flagged[np.argsort(-maxlogk[flagged])]

    tot = sumw[sumw > 0].sum()
    print(f"# card:      {args.card}")
    print(f"# process:   {args.process}   (index {ip} of {procs})")
    print(
        f"# flag rule: any syst with |logk| > log({args.threshold}) "
        f"= {log_thr:.3f}  (i.e. > {args.threshold:g}x or < {1/args.threshold:g}x)"
    )
    print(
        f"# {args.process} total yield = {tot:.1f} events "
        f"over {(sumw > 0).sum()} populated bins"
    )
    print(
        f"# flagged bins: {len(flagged)}  "
        f"carrying {sumw[flagged].sum():.4g} events "
        f"({100 * sumw[flagged].sum() / tot:.3f}% of {args.process})"
    )
    if len(flagged):
        print(
            f"# of flagged: n_eff<1: {(neff[flagged] < 1).sum()}  "
            f"n_eff<0.01: {(neff[flagged] < 0.01).sum()}  "
            f"max n_eff: {neff[flagged].max():.3g}"
        )
    print()

    hdr = (
        f"{'bin':>7} {'yield(sumw)':>12} {'sqrt(sumw2)':>12} {'n_eff':>10} "
        f"{'max|logk|':>9}  {'worst syst':<34} coords"
    )
    print(hdr)
    print("-" * len(hdr))
    show = flagged if args.top == 0 else flagged[: args.top]
    for B in show:
        _, coords = locate(chans, B)
        cstr = " ".join(f"{nm}=[{lo:g},{hi:g})" for (nm, lo, hi, i) in coords)
        print(
            f"{B:>7} {sumw[B]:12.4g} {np.sqrt(sumw2[B]):12.4g} {neff[B]:10.2e} "
            f"{maxlogk[B]:9.3f}  {systs[argsyst[B]]:<34} {cstr}"
        )
    if args.top and len(flagged) > args.top:
        print(
            f"\n# ... {len(flagged) - args.top} more flagged bins "
            f"(use --top 0 to show all)"
        )

    if args.by_syst:
        report_by_syst(
            args,
            systs,
            trips_per_syst,
            trips_per_bin,
            flagged,
            sumw,
            neff,
            chans,
            ip,
            NPROC,
            NS,
            log_thr,
            maxlogk_syst,
            argbin_syst,
        )


def report_by_syst(
    args,
    systs,
    trips_per_syst,
    trips_per_bin,
    flagged,
    sumw,
    neff,
    chans,
    ip,
    NPROC,
    NS,
    log_thr,
    maxlogk_syst,
    argbin_syst,
):
    """Same bins, or different bins for different systematics?"""
    NB = 15
    total_trips = int(trips_per_syst.sum())
    n_bins_tripped = int((trips_per_bin > 0).sum())
    n_systs_tripping = int((trips_per_syst > 0).sum())

    print("\n" + "=" * 70)
    print("BY-SYSTEMATIC CROSS-TAB  (do systs trip the SAME bins or different?)")
    print("=" * 70)
    print(f"distinct bins tripped by >=1 syst : {n_bins_tripped}")
    print(f"systematics that trip >=1 bin      : {n_systs_tripping} / {NS}")
    print(f"total (syst,bin) trip pairs        : {total_trips}")
    print(
        f"avg systs per tripped bin          : {total_trips / max(n_bins_tripped,1):.1f}"
    )

    # --- how many systs trip each bin (concentration -> "same bins") ---
    tb = trips_per_bin[trips_per_bin > 0]
    print("\nper-bin: how many systematics trip the same bin")
    for lo, hi, lab in [
        (1, 1, "  1 syst"),
        (2, 5, "  2-5"),
        (6, 20, "  6-20"),
        (21, 100, " 21-100"),
        (101, NS, ">100"),
    ]:
        m = (tb >= lo) & (tb <= hi)
        print(f"  tripped by {lab:>8} syst(s): {int(m.sum()):5d} bins")
    order_shared = flagged[np.argsort(-trips_per_bin[flagged])]
    topbins = order_shared[:NB]
    frac = 100 * trips_per_bin[topbins].sum() / max(total_trips, 1)
    print(f"  -> the {NB} most-tripped bins account for {frac:.1f}% of all trip pairs")

    # break down each shared-core bin into resolution vs other tripping systs
    print(f"\ntop {NB} shared-core bins (tripped by the most systematics):")
    hdr = (
        f"{'bin':>7} {'#systs':>6} {'#res':>5} {'#other':>6} "
        f"{'yield':>10} {'n_eff':>9}  coords"
    )
    print(hdr)
    print("-" * len(hdr))
    with h5py.File(args.card, "r") as f:
        ds = f["hlogk"]
        for B in topbins:
            row = np.abs(ds[(B * NPROC + ip) * NS : (B * NPROC + ip) * NS + NS])
            trip_idx = np.where(row > log_thr)[0]
            nres = sum(
                1
                for i in trip_idx
                if systs[i].startswith("Resolution_correction_smearing")
            )
            _, coords = locate(chans, B)
            cstr = " ".join(f"{nm}#{i}" for (nm, lo, hi, i) in coords)
            print(
                f"{B:>7} {len(trip_idx):>6} {nres:>5} {len(trip_idx)-nres:>6} "
                f"{sumw[B]:10.4g} {neff[B]:9.2e}  {cstr}"
            )

    # --- which systs cause the LARGEST variation (the actual hazard) ---
    print(
        f"\ntop {NB} systematics by SIZE of their largest variation "
        f"(max|logk| -> up-factor), i.e. most problematic:"
    )
    hdr2 = (
        f"{'max|logk|':>9} {'up-factor':>12} {'#bins':>6}  "
        f"{'worst bin':>9} {'yield':>10} {'n_eff':>9}  systematic"
    )
    print(hdr2)
    print("-" * len(hdr2))
    order_s = np.argsort(-maxlogk_syst)
    for i in order_s[:NB]:
        if maxlogk_syst[i] <= log_thr:
            break
        B = argbin_syst[i]
        print(
            f"{maxlogk_syst[i]:9.3f} {np.exp(maxlogk_syst[i]):12.4g} "
            f"{trips_per_syst[i]:6d}  {B:>9} {sumw[B]:10.4g} {neff[B]:9.2e}  "
            f"{systs[i]}"
        )

    # --- rollup by systematic family ---
    fam_trips, fam_nsyst = {}, {}
    for i in range(NS):
        if trips_per_syst[i] == 0:
            continue
        fam = syst_family(systs[i])
        fam_trips[fam] = fam_trips.get(fam, 0) + int(trips_per_syst[i])
        fam_nsyst[fam] = fam_nsyst.get(fam, 0) + 1
    print("\ntrip pairs by systematic family (which families misbehave):")
    print(f"  {'family':<32} {'#systs':>7} {'trip pairs':>11}")
    for fam in sorted(fam_trips, key=lambda k: -fam_trips[k])[:NB]:
        print(f"  {fam:<32} {fam_nsyst[fam]:>7} {fam_trips[fam]:>11}")

    print(
        "\nread: a large 'avg systs per tripped bin' + high top-bin trip-pair "
        "share => the SAME near-empty bins are hit by MANY systs (shared core). "
        "Bins tripped by only 1 syst => that syst's smearing moved events into a "
        "cell others leave empty (a private tail)."
    )


if __name__ == "__main__":
    main()
