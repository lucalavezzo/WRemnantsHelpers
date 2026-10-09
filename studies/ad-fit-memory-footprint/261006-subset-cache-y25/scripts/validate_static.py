#!/usr/bin/env python3
"""Static, byte-level validation of a |Y|-subset cache against its source.

Checks, for EVERY kept bin:
  rules  the record bytes in the subset's cache.rules.bin equal the source record bytes (direct compare,
         64 MB chunks), its key is bins_sub[i], and it parses EXACTLY with SCETlib's own
         scetlib_cache._parse_rules as a one-bin blob (header + n=1 + record). The header up to n_bins is
         byte-identical to the source's, and n_bins = len(bins_sub).
  fo     with scetlib_cache.parse_fo_blob on both blobs: version, fingerprint, meta, bilin header identical;
         per kept bin: frozen grid node block, muF-poly block (every window), the 9-double member deltas of all
         60 members, the quadratic-form slice B[:, :, :, bin, :], and the group-resolved (mu, data) rows --
         all byte-identical to the source bin with the same key. No key outside the kept set anywhere.
  npz    format/n_eig/has_as/has_muf/anchor/names raw .npy bytes identical; bins_sub == source bins[Y_hi<=ymax]
         bitwise and in source order; the rules member's CRC/sizes match the .rules.json sidecar.
  conf   differs from the source only in the leading comment and the Grid_Y values.
usage: validate_static.py --src DIR --sub DIR [--ymax 2.5] [--json out.json]
"""
import argparse
import difflib
import json
import os
import sys
import time
import zipfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_io  # noqa: E402
import scetlib_cache  # noqa: E402

SMALL = ("format", "n_eig", "has_as", "has_muf", "anchor", "names")
CHUNK = 1 << 26


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def same_range(fa, sa, fb, sb, n):
    fa.seek(sa)
    fb.seek(sb)
    while n:
        k = min(n, CHUNK)
        if fa.read(k) != fb.read(k):
            return False
        n -= k
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--sub", required=True)
    ap.add_argument("--ymax", type=float, default=2.5)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    R = {}
    fails = []

    def check(name, ok, detail=""):
        R[name] = bool(ok)
        log(("PASS " if ok else "FAIL ") + name + (f"  {detail}" if detail else ""))
        if not ok:
            fails.append(name)

    snpz, unpz = os.path.join(a.src, "cache.npz"), os.path.join(a.sub, "cache.npz")
    with zipfile.ZipFile(snpz) as zs, zipfile.ZipFile(unpz) as zu:
        check(
            "npz member list/order identical",
            [i.filename for i in zs.infolist()] == [i.filename for i in zu.infolist()],
            str([i.filename for i in zu.infolist()]),
        )
        for k in SMALL:
            check(
                f"npz {k}.npy raw bytes identical",
                zs.read(k + ".npy") == zu.read(k + ".npy"),
            )
        ri = zu.getinfo("rules.npy")
        side = json.load(open(os.path.join(a.sub, "cache.rules.json")))
        check(
            "rules sidecar matches the subset npz rules member",
            (ri.CRC, ri.file_size, ri.compress_size)
            == (side["crc32"], side["file_size"], side["compress_size"])
            and os.path.getsize(os.path.join(a.sub, "cache.rules.bin"))
            == side["payload_bytes"],
        )
    with np.load(snpz) as d:
        bs = np.ascontiguousarray(d["bins"], "<f8")
        fo_s = d["fo"].tobytes()
    with np.load(unpz) as d:
        bu = np.ascontiguousarray(d["bins"], "<f8")
        fo_u = d["fo"].tobytes()
    keep = np.flatnonzero(bs[:, 3] <= a.ymax + 1e-12)
    check(
        "bins == source bins[Y_hi<=ymax], bitwise, source order",
        bu.shape == (keep.size, 6)
        and np.array_equal(bu.view(np.uint64), bs[keep].view(np.uint64)),
        f"{bu.shape[0]} of {bs.shape[0]}",
    )
    check(
        "subset max Y_hi <= ymax",
        float(bu[:, 3].max()) <= a.ymax + 1e-12,
        f"{bu[:, 3].max()}",
    )
    src_index = {bs[j].tobytes(): j for j in range(bs.shape[0])}

    # ---- rules ----
    t0 = time.time()
    Ws = cache_io.walk_rules(os.path.join(a.src, "cache.rules.bin"))
    Wu = cache_io.walk_rules(os.path.join(a.sub, "cache.rules.bin"))
    log(f"walked both rule files in {time.time() - t0:.1f} s")
    check(
        "rules header (magic..member identities) byte-identical",
        Ws["header"] == Wu["header"],
    )
    check("rules n_bins == len(bins)", Wu["n_bins"] == bu.shape[0], f"{Wu['n_bins']}")
    check(
        "rules keys == bins, in order",
        all(Wu["records"][i][2] == bu[i].tobytes() for i in range(bu.shape[0])),
    )
    opts_size = len(
        scetlib_cache.parse_rule_blob(Ws["header"] + cache_io.U64.pack(0))["opts_raw"]
    )
    nbad, nparse_bad = 0, 0
    tot = 0
    with (
        open(os.path.join(a.src, "cache.rules.bin"), "rb") as fs,
        open(os.path.join(a.sub, "cache.rules.bin"), "rb") as fu,
    ):
        for i, (s, e, key) in enumerate(Wu["records"]):
            js = src_index[key]
            ss, se, sk = Ws["records"][js]
            assert sk == key
            if (e - s) != (se - ss) or not same_range(fu, s, fs, ss, e - s):
                nbad += 1
            fu.seek(s)
            rec = fu.read(e - s)
            tot += e - s
            try:
                p = scetlib_cache._parse_rules(
                    Wu["header"] + cache_io.U64.pack(1) + rec, opts_size
                )
                if len(p["rules"]) != 1 or p["rules"][0]["key"] != key:
                    nparse_bad += 1
            except Exception as ex:  # noqa: BLE001
                nparse_bad += 1
                log(f"  record {i} does not parse: {ex}")
            del rec
            if i % 100 == 0:
                log(
                    f"  rules record {i}/{len(Wu['records'])}  {tot / 1e9:.1f} GB  {time.time() - t0:.0f} s"
                )
    check(
        "every kept rule record byte-identical to the source record",
        nbad == 0,
        f"{nbad} differ of {len(Wu['records'])}",
    )
    check(
        "every kept rule record parses exactly with scetlib_cache._parse_rules",
        nparse_bad == 0,
        f"{nparse_bad} bad",
    )
    check(
        "subset rules file = header + n + kept records (no extra bytes)",
        Wu["end"] == Wu["nb_pos"] + 8 + tot,
        f"{Wu['end']} B",
    )
    R["rules_bytes"] = dict(
        src=Ws["end"],
        sub=Wu["end"],
        src_sites=sum(Ws["n_sites"]),
        sub_sites=sum(Wu["n_sites"]),
    )

    # ---- fo ----
    Ps, Pu = scetlib_cache.parse_fo_blob(fo_s), scetlib_cache.parse_fo_blob(fo_u)
    check(
        "fo version/fingerprint/meta identical",
        (Ps["version"], Ps["fingerprint"], Ps["meta"])
        == (Pu["version"], Pu["fingerprint"], Pu["meta"]),
    )
    vu = np.asarray(Pu["var_bins"]).reshape(-1, 6)
    check(
        "fo var_bins == bins (same order as the rules)",
        np.array_equal(vu.view(np.uint64), bu.view(np.uint64)),
    )
    keys = [bu[i].tobytes() for i in range(bu.shape[0])]
    kset = set(keys)
    check("fo grid keys == kept keys", set(Pu["grid"]) == kset)
    check(
        "fo grid node blocks byte-identical per bin",
        all(Pu["grid"][k] == Ps["grid"][k] for k in keys),
    )
    check("fo muF-poly windows identical set", list(Pu["poly"]) == list(Ps["poly"]))
    okp = True
    for j0 in Ps["poly"]:
        want = {k: v for k, v in Ps["poly"][j0].items() if k in kset}
        okp &= list(Pu["poly"][j0].items()) == list(want.items())
    check(
        "fo muF-poly blocks byte-identical per bin (source order), no extra keys", okp
    )
    nb_s = bs.shape[0]
    jidx = np.array([src_index[k] for k in keys])
    check(
        "fo member count identical",
        len(Pu["deltas"]) == len(Ps["deltas"]),
        f"{len(Pu['deltas'])}",
    )
    okd = all(
        np.frombuffer(du, "<f8").reshape(-1, 9).tobytes()
        == np.frombuffer(ds, "<f8").reshape(nb_s, 9)[jidx].tobytes()
        for du, ds in zip(Pu["deltas"], Ps["deltas"])
    )
    check("fo member deltas (9 doubles/bin, every member) byte-identical per bin", okd)
    bS, bU = Ps["bilin"], Pu["bilin"]
    check(
        "fo quadratic-form header identical",
        (bS["nd"], bS["nmuf"], bS["as_anchor"], bS["n_eig"])
        == (bU["nd"], bU["nmuf"], bU["as_anchor"], bU["n_eig"]),
    )
    check(
        "fo quadratic-form bins == bins",
        np.array_equal(
            np.asarray(bU["bins"]).reshape(-1, 6).view(np.uint64), bu.view(np.uint64)
        ),
    )
    BS = np.asarray(bS["B"]).reshape(bS["nmuf"], bS["nd"], bS["nd"], nb_s, 9)
    BU = np.asarray(bU["B"]).reshape(bU["nmuf"], bU["nd"], bU["nd"], len(keys), 9)
    check(
        "fo quadratic form B[:, :, :, bin, :] byte-identical per bin (incl. the bin0xzero zeros)",
        np.ascontiguousarray(BS[:, :, :, jidx, :]).tobytes() == BU.tobytes(),
    )
    # the bin0xzero patch is still there: qT [0, 0.5] bins have every off-diagonal d1 != d2 >= 1 entry zero
    q0 = np.flatnonzero(bu[:, 4] == 0.0)
    off = np.ones((bU["nd"], bU["nd"]), bool)
    off[0, :] = off[:, 0] = False
    np.fill_diagonal(off, False)
    z = BU[:, :, :, q0, :][:, off, :, :]
    check(
        "bin0xzero patch present: qT[0,0.5] off-diagonal form entries all zero",
        q0.size == 11 and not np.any(z),
        f"{q0.size} bins, max|.|={np.abs(z).max() if z.size else 0}",
    )
    zs_ = np.abs(BS[:, :, :, np.flatnonzero(bs[:, 4] == 0.0), :][:, off, :, :]).max()
    R["src_bin0_offdiag_max"] = float(zs_)
    okg = len(Pu["var_g"]) == len(keys) and all(
        Pu["var_g"][i][0].tobytes() == Ps["var_g"][jidx[i]][0].tobytes()
        and Pu["var_g"][i][1].tobytes() == Ps["var_g"][jidx[i]][1].tobytes()
        for i in range(len(keys))
    )
    check("fo group-resolved member rows (mu, data) byte-identical per bin", okg)

    # ---- conf ----
    cs = open(os.path.join(a.src, "cache.conf")).read().splitlines()
    cu = open(os.path.join(a.sub, "cache.conf")).read().splitlines()
    dl = [
        l
        for l in difflib.unified_diff(cs, cu, lineterm="", n=0)
        if l[:1] in "+-" and l[:3] not in ("+++", "---")
    ]
    ok = (
        all(l.startswith(("+#", "-values", "+values")) for l in dl)
        and sum(l.startswith("-values") for l in dl) == 1
    )
    check(
        "cache.conf differs only by the comment + one Grid_Y values line",
        ok,
        " | ".join(dl),
    )

    R["fails"] = fails
    if a.json:
        json.dump(R, open(a.json, "w"), indent=1)
    log("ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
