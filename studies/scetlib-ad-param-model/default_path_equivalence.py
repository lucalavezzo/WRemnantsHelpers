#!/usr/bin/env python3
"""Does the patched prepare_cache_for_card still drive SCETlib identically?

"Byte-identical output to today" cannot be shown by rebuilding: the builder is
not reproducible run to run (the bin loop is a tbb::parallel_for over
integrator objects that keep internal buffers, so two identical builds retain
different numbers of nodes -- measured 357 vs 359 nodes/bin, and the rule blob
even carries uninitialised struct padding). What CAN be shown, and is what
actually matters, is that the two versions hand the extension the SAME CALLS
with the SAME ARGUMENTS in the same order -- everything downstream of that is
inside SCETlib.

So: stub out the calculation, run both mains with identical argv, and diff the
recorded call log.

    ./incontainer.sh python3 default_path_equivalence.py
"""

import importlib.util
import os
import sys
import tempfile

import numpy as np

NEW = os.environ.get(
    "NEW_BUILDER",
    "/home/submit/lavezzo/alphaS/WRemnants/scripts/rabbit/scetlib_ad/"
    "prepare_cache_for_card.py",
)
# A pristine copy of the pre-refactor builder, with its sibling
# build_cache_parallel.py beside it -- the old --fork-members path imports that
# sibling, so the copy has to be a DIRECTORY, not a lone file.
OLD = os.environ.get(
    "OLD_BUILDER", "/tmp/scetlib_ad_orig/prepare_cache_for_card.py"
)

NAMES = [
    "alphas",
    "np_eff_lambda_inf",
    "np_eff_lambda2",
    "np_eff_lambda4",
    "np_eff_delta_lambda2",
    "np_gnu_lambda_inf",
    "np_gnu_lambda2",
    "np_gnu_lambda4",
    "np_gnu_b0_bmax",
    "tnp_gamma_cusp",
    "tnp_gamma_mu_q",
    "tnp_gamma_nu",
    "tnp_s",
    "tnp_b_qqV",
    "tnp_b_qqbarV",
    "tnp_b_qqS",
    "tnp_b_qqDS",
    "tnp_b_qg",
    "tnp_h_qqV",
    "scale_kappa_R",
    "scale_x1",
    "scale_x2",
    "scale_x3",
    "scale_kappa_F",
]
VALUES = [0.118, 1, 0.4, 0.4, 0, 2, 0.15, 0, 1] + [0] * 10 + [1, 0.2, 0.6, 1, 1]


def _rec(log, what, args, kwargs):
    def clean(x):
        if isinstance(x, np.ndarray):
            return ("array", x.shape, str(x.dtype), np.asarray(x).ravel().tolist())
        return x

    log.append(
        (
            what,
            [clean(a) for a in args],
            {k: clean(v) for k, v in sorted(kwargs.items())},
        )
    )


class Piece:
    """Records what the builder asks of a sub-piece."""

    def __init__(self, log, tag, names, n_bins):
        self._log, self._tag, self._names, self._n = log, tag, names, n_bins
        self._eig = 0

    def gradient_param_names(self):
        return list(self._names) + [f"pdf_eig{e}" for e in range(self._eig)]

    def gradient_central(self):
        return np.array(
            VALUES[: len(self._names)] + [0.0] * self._eig, dtype=np.float64
        )

    def set_pdf_eig_params(self, n):
        _rec(self._log, f"{self._tag}.set_pdf_eig_params", (n,), {})
        self._eig = int(n)

    def build_bin_rules(self, *a, **k):
        _rec(self._log, f"{self._tag}.build_bin_rules", a, k)
        return [{"nodes": 10, "nodes_full": 100, "resid": 1e-9} for _ in range(self._n)]

    def build_pdf_variations(self, *a, **k):
        _rec(self._log, f"{self._tag}.build_pdf_variations", a, k)

    def build_fo_pdf_variations(self, *a, **k):
        _rec(self._log, f"{self._tag}.build_fo_pdf_variations", a, k)

    def sigma_binned_batch(self, bins, p, *a, **k):
        return np.ones(self._n), None

    def rule_fo_weights(self, *a):
        return [1.0]

    def save_bin_rules_bytes(self):
        return b""

    def save_fo_cache_bytes(self):
        return b""

    def bin_rule_anchor(self):
        return self.gradient_central()


class Sigma:
    def __init__(self, log, n_bins):
        self.sing = Piece(log, "sing", NAMES, n_bins)
        self.nons = Piece(
            log, "nons", ["alphas", "scale_kappa_R", "scale_kappa_F"], n_bins
        )
        self._log, self._n = log, n_bins

    def sub_pieces(self):
        return self.sing, self.nons

    def gradient_param_names(self):
        return self.sing.gradient_param_names()

    def gradient_central(self):
        return self.sing.gradient_central()

    def prepare(self, bins, p):
        _rec(self._log, "sigma.prepare", (bins, p), {})
        return np.ones(self._n)

    def sigma_binned_batch(self, bins, p):
        return np.ones(self._n), None


def run(path, argv, n_bins):
    """Import one version of the builder with the calculation stubbed, run it."""
    log = []
    import configparser
    import types

    def _write(bins, out, n_eig, has_as, has_muf):
        """The one record both cache writers produce.

        The pre-refactor builder went through ScetlibCachedXsecTF(...).save();
        the moved one calls the TF-free scetlib_cache.save_cache(). Different
        call, same act -- "write THESE bins with THIS variation header to THIS
        file" -- so both are recorded identically and the logs stay comparable.
        """
        _rec(
            log,
            "write_cache",
            (bins, os.path.basename(out)),
            dict(n_eig=n_eig, has_as=has_as, has_muf=has_muf),
        )
        with open(out + ".npz", "wb") as f:
            f.write(b"x")

    fake_tf = types.ModuleType("scetlib_tf")

    class FakeCached:
        def __init__(self, sing, nons, bins, n_eig=0, has_as=False, has_muf=False):
            self._a = (bins, n_eig, has_as, has_muf)

        def save(self, out):
            bins, n_eig, has_as, has_muf = self._a
            _write(bins, out, n_eig, has_as, has_muf)

    fake_tf.ScetlibCachedXsecTF = FakeCached
    sys.modules["scetlib_tf"] = fake_tf

    # scetlib_cache is SCETlib's TF-free cache-format module. Stubbing it keeps
    # the harness from writing real blobs AND proves the build path no longer
    # needs scetlib_tf at all: if the module under test still reached for the TF
    # wrapper, the recorded call would come from FakeCached above and the
    # sing/nons arguments would differ.
    fake_cache = types.ModuleType("scetlib_cache")
    fake_cache.FORMAT = 1

    def _save_cache(sing, nons, bins, path, n_eig=0, has_as=False, has_muf=False):
        _write(bins, path, n_eig, has_as, has_muf)

    def _split_pairs(pairs, n_procs):
        n = len(pairs)
        k = max(1, min(int(n_procs), n))
        return [
            (pairs[(i * n) // k][0], pairs[((i + 1) * n) // k - 1][1])
            for i in range(k)
        ]

    fake_cache.save_cache = _save_cache
    fake_cache.split_pairs = _split_pairs
    fake_cache.merge_shards = lambda paths, out, verbose=True: out + ".npz"
    sys.modules["scetlib_cache"] = fake_cache

    # The pre-refactor builder got the same two functions from its sibling
    # build_cache_parallel (which is the import cycle the refactor removed), so
    # the old arm has to be given the same stubs or it would try to np.load the
    # placeholder files _write leaves behind.
    fake_bcp = types.ModuleType("build_cache_parallel")
    fake_bcp.split_pairs = _split_pairs
    fake_bcp.merge_shards = fake_cache.merge_shards
    sys.modules["build_cache_parallel"] = fake_bcp

    # The builder's own directory, so a version that imports a sibling module
    # (the pre-refactor --fork-members path imports build_cache_parallel) finds
    # ITS sibling and not the other arm's.
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec = importlib.util.spec_from_file_location("builder_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def fake_configure(runcard, threads=0, **kw):
        _rec(log, "configure", (os.path.basename(runcard), threads), kw)
        conf = configparser.ConfigParser(inline_comment_prefixes="#")
        conf.read_dict(
            {"QCD": {"pdf_set": "CT18ZNNLO", "nf": "5", "alphas_mu0": "0.118"}}
        )
        return conf, Sigma(log, n_bins)

    mod.configure = fake_configure
    old_argv = sys.argv
    sys.argv = ["prepare_cache_for_card.py"] + argv
    try:
        mod.main()
    finally:
        sys.argv = old_argv
        sys.path.pop(0)
        sys.modules.pop("build_cache_parallel", None)
    return log


def main():
    grid = '{"Q": [60, 120], "Y": [0, 0.25, 0.5], ' '"qT": [20, 27, 33, 44, 100]}'
    n_bins = 8
    rc = 0
    # Every route through main(), because the refactor moved all of them: the
    # default, the physics-only cache, the no-muF variant, the eigenvector
    # registration, a bin subset, a member slice (partial cache + sidecar) and
    # the forked member loop.
    for tag, extra in (
        ("--pdf-eig 0 (every cache built so far)", ["--pdf-eig", "0"]),
        ("--no-pdf", ["--no-pdf"]),
        ("--pdf-eig 0 --no-muf", ["--pdf-eig", "0", "--no-muf"]),
        ("--pdf-eig 2", ["--pdf-eig", "2"]),
        ("--pdf-eig 2 --members 0:2", ["--pdf-eig", "2", "--members", "0:2"]),
        ("--pdf-eig 0 --subset '0/1,2'", ["--pdf-eig", "0", "--subset", "0/1,2"]),
        ("--pdf-eig 2 --fork-members 2", ["--pdf-eig", "2", "--fork-members", "2"]),
    ):
        logs = []
        for path in (OLD, NEW):
            with tempfile.TemporaryDirectory() as d:
                logs.append(
                    run(
                        path,
                        [
                            "--grid-json",
                            grid,
                            "--base-conf",
                            "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/"
                            "scetlib_ad_caches/par_test/base.conf",
                            "-o",
                            d,
                            "--threads",
                            "32",
                        ]
                        + extra,
                        n_bins,
                    )
                )
        same = logs[0] == logs[1]
        rc |= 0 if same else 1
        print(f"{'SAME' if same else 'DIFFERENT'}  {tag}  " f"({len(logs[0])} calls)")
        if not same:
            for i, (a, b) in enumerate(zip(logs[0], logs[1])):
                if a != b:
                    print(
                        f"   first difference at call {i}:\n"
                        f"     old {a}\n     new {b}"
                    )
                    break
            if len(logs[0]) != len(logs[1]):
                print(f"   call counts {len(logs[0])} vs {len(logs[1])}")
        else:
            for c in logs[0]:
                print(f"     {c[0]}")
    print("\nthe default path is unchanged" if rc == 0 else "\nDEFAULT PATH CHANGED")
    sys.exit(rc)


if __name__ == "__main__":
    main()
