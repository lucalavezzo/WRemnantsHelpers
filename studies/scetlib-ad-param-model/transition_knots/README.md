# transition_knots -- the 2026-08-25 (later) round on the transition derivative

Everything here was written for the round that measured the muF knot spacing
with the member COORDINATE fix in place. See the staged logbook entry (in the
session tmp dir) and
`~/public_html/alphaS/260825_transition_muf_coordinate_fix/00_README.txt`.

## Builds (isolated on purpose -- several agents were live)

| worktree | branch / commit | build dir | what it is |
|---|---|---|---|
| `/work/submit/lavezzo/alphaS/scetlib-nak` | `near-anchor-knots` | `build-nak` | `bb2e7cb` + `92f1299` (muF member coordinate) + `83cecb2` (knot spacing, = `e61a8d0`) + `3a8db11` (= `59bc17b`) + `eb60a04` (DIAGNOSTIC `rule_cvals()`) |
| `/work/submit/lavezzo/alphaS/scetlib-nakbase` | detached `e61a8d0` | `build-nakbase` | the BEFORE arm -- differs from the above by exactly `92f1299` |

`scetlib-cms`, `build-fix`, `build-knots`, `build-trans` were NOT touched.

## Running anything

The node's 32768-threads-per-user ceiling was ~99% consumed by other sessions.
Use `incontainer_nak_lean.sh` (all thread pools pinned to 2) and `--threads 8`,
and run at most TWO SCETlib processes at once, or they abort with
`pthread_create has failed: Resource temporarily unavailable`.

## The scripts

| file | what it answers |
|---|---|
| `stencil_geometry.py` | pure arithmetic: where the transition-induced per-node ln(muF) shift sits inside the muF member stencil. No SCETlib. |
| `plot_stencil.py` | the mechanism figures, one per qT bin |
| `knot_interp_error.py` | the model against an EXACT runcard refill at a settable knot spacing (copied from `../knot_scan/`, unmodified) |
| `run_interp_nak.sh` | one (x2, knot) point of the above |
| `plot_knot_response.py` | the response plot, model vs the runcard reference, several knot spacings |
| `model_vs_template_perbin.py` / `run_perbin.sh` | per-bin model-vs-TEMPLATE response and the CENTRAL shape (the confound test). Cache + corr only. |
| `decompose.py` | ours / theirs / total, and the two model instances against each other |
| `cval_from_cache.py` / `run_cval_cache.sh` | how big the rule's dead constant `c_val` is, on the production cache. Needs the `rule_cvals()` diagnostic commit. |
| `cval_size.py` | the same on live-built rules (no cache) |
| `run_validate_nak.sh` | `validate_variations.py` on cache_260824b through either build |

Outputs:
`/ceph/.../scetlib_ad_caches/knot_scan/nak/*.json`.

---

## 2026-08-26 -- the FIVE-KNOT round (`fiveknot_*`)

Everything named `fiveknot_*` plus `prepare_cache_5knot.py`,
`run_cache_5knot.sh`, `configure_5knot.sh`, `incontainer_5knot.sh` belongs to
the muF knot-COUNT round. Webdir
`~/public_html/alphaS/260825_muf_five_knots/00_README.txt`; staged logbook entry
in that session's tmp dir.

| worktree | branch / commit | build dir |
|---|---|---|
| `/work/submit/lavezzo/alphaS/scetlib-5knot` | `muf-five-knots` `61123f2` | `build-5knot` |

Off `eb60a04`, i.e. `near-anchor-knots`. `scetlib-cms`, `build-fix`,
`build-knots`, `build-trans`, `build-nak`, `build-nakbase` were NOT touched.

| file | what it answers |
|---|---|
| `fiveknot_interp_error.py` | 3 vs 5 knots against an EXACT runcard refill, both arms in ONE process off the same members |
| `fiveknot_kappaF_error.py` | kappa_F BETWEEN the knots against a runcard refill -- the sharp test, since kappa_F = sqrt2 is a knot of one stencil only |
| `fiveknot_closure.py` | the CorrZ closure A/B from ONE cache, via `set_muf_knots_used` |
| `fiveknot_stencil_geometry.py` | where the transition-induced per-node shift sits relative to all three knot geometries. Arithmetic only |
| `fiveknot_plot_stencil.py` | the mechanism figures from the above |
| `prepare_cache_5knot.py` | `prepare_cache_for_card.py` with `MUF_NMEM` / `MUF_KNOT` overrides |

**Two traps that cost time and would cost it again.**
1. `ScetlibCachedXsecTF.values_and_jacobian` memoises on the PARAMETER VECTOR
   alone. `set_muf_knots_used` is not in that key, so two arms evaluated back to
   back at the same p return the FIRST arm's numbers for both -- a perfect null,
   indistinguishable from "the change does nothing". `fiveknot_closure.py`
   carries a hard guard against it (a kappa_F = sqrt2 probe that MUST separate).
2. Any global the kernel reads must NOT be `thread_local`: `_stage_var_meta`
   runs inside the TBB workers of `_ad_parallel_run`.
