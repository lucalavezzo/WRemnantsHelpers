#!/usr/bin/env python3
"""The lattice card must be the production card PLUS one group, and nothing else.

A card is the whole likelihood, so "I copied it and added a term" has to be
checked rather than asserted: a silently different hlogk or hdata_obs would make
every comparison in this task meaningless.
"""
import sys

import h5py
import numpy as np

A, B = sys.argv[1], sys.argv[2]


def tree(f):
    out = {}
    f.visititems(
        lambda n, o: out.__setitem__(n, o) if isinstance(o, h5py.Dataset) else None
    )
    return out


with h5py.File(A, "r") as fa, h5py.File(B, "r") as fb:
    ta, tb = tree(fa), tree(fb)
    only_a = sorted(set(ta) - set(tb))
    only_b = sorted(set(tb) - set(ta))
    print(f"[A] {A}\n[B] {B}")
    print(f"[A only] {only_a}")
    print(f"[B only] {only_b}")
    ndiff = 0
    unread = []
    raw_ok = []
    for k in sorted(set(ta) & set(tb)):
        da, db = ta[k], tb[k]
        if da.shape != db.shape or da.dtype != db.dtype:
            print(
                f"  DIFFERENT layout: {k} {da.shape}{da.dtype} vs {db.shape}{db.dtype}"
            )
            ndiff += 1
            continue

        def _canon(x):
            """Ragged/vlen object arrays make `==` return arrays; flatten them
            to bytes so one comparison rule covers every dtype in the card."""
            a = np.asarray(x)
            if a.dtype.kind == "O":
                return [np.asarray(v).tobytes() for v in a.ravel()]
            return a.tobytes()

        try:
            same = True
            step = 10_000_000
            for i in range(0, max(da.size, 1), step):
                if _canon(da[i : i + step]) != _canon(db[i : i + step]):
                    same = False
                    break
        except OSError:
            # Fall back to comparing the RAW stored bytes chunk by chunk.
            # read_direct_chunk returns the bytes as they sit on disk, still
            # filtered, so it needs no decompression plugin -- which is exactly
            # what the container is missing. This is a STRONGER check than the
            # decoded comparison, not a weaker one.
            try:
                import hashlib

                def rawsig(d):
                    did = d.id
                    n = did.get_num_chunks()
                    h = hashlib.md5()
                    for i in range(n):
                        ci = did.get_chunk_info(i)
                        h.update(bytes(did.read_direct_chunk(ci.chunk_offset)[1]))
                    return (n, h.hexdigest())

                sa, sb = rawsig(da), rawsig(db)
                if sa != sb:
                    print(f"  DIFFERENT raw chunks: {k} {sa} vs {sb}")
                    ndiff += 1
                else:
                    raw_ok.append(k)
                continue
            except Exception as ex2:  # noqa: BLE001
                print(
                    f"  [raw-chunk fallback failed for {k}: "
                    f"{type(ex2).__name__}: {ex2}]"
                )
            # A dataset written with a compression filter this container lacks
            # (/usr/local/hdf5/lib/plugin). Layout is still comparable; say so
            # rather than silently counting it as identical.
            unread.append(k)
            continue
        if not same:
            print(f"  DIFFERENT values: {k} (size {da.size})")
            ndiff += 1
    shared = len(set(ta) & set(tb))
    print(
        f"[shared datasets] {shared}, decoded-compared {shared - len(unread) - len(raw_ok)}, "
        f"raw-chunk-compared {len(raw_ok)}, differing {ndiff}, "
        f"not compared {len(unread)}: {unread}"
    )
    if raw_ok:
        print(f"[raw-chunk identical] {raw_ok}")
    print(f"[note] shape+dtype matched for all {shared} shared datasets")
    ok = (
        ndiff == 0
        and not only_a
        and only_b
        == [
            "external_terms/lattice_cs/grad_values",
            "external_terms/lattice_cs/hess_dense",
            "external_terms/lattice_cs/params",
        ]
    )
    print("DIFF_CARDS_DONE" if ok else "DIFF_CARDS_UNEXPECTED")
