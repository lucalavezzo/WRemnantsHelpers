---
task: adopt-joshhead
updated: 2026-09-08
---

# Adopt Josh's head + our MR !11

## START HERE

**State.** Built and central-verified. `8e92c14` = `dce84b1` (Josh's head,
2026-09-08) + our MR !11, i.e. the `hvp-fast-covariance` branch head, at
`/work/submit/lavezzo/alphaS/scetlib-ad-joshhead-260908`. `libscet-qT.so` md5
`4d658b6d1b3589c81c6fa977919d5e13` (the validated `b66f8de` was
`71b5e68a0cfed89326ff4ed521d37300`).

**The two things that decide the cost of adoption, both answered:**

| question | answer |
|---|---|
| does the 770-bin cache survive? | **YES** -- `struct GlobalData` is byte-identical, so `sizeof(ad::GlobalData)` (the rule-cache POD guard) is unchanged |
| does the central prediction move? | **NO** -- bit-for-bit identical, see Findings |

**Next step.** The gen-variation comparison is running (97 directions). That is
the last open question, because muF/kappa_F and the transitions are exactly
where MR !8/!9 lived. `b66f8de` gave worst 3.09e-02 (`mufup`).

**Blocking.** Nothing. But see the kappa_F warning in Decisions before quoting
any muF-direction uncertainty from this library.

## Findings

### The central prediction is unchanged, bit-for-bit

Same cache, same reference (`..._CT18Z_N3p0LL_N2LO_CorrZ.pkl.lz4`), same script
(`compare_to_scetlib_run.py --piece matched`); the library is the only variable.

| library | total ours/ref | median \|dev\| | max \|dev\| |
|---|---|---|---|
| `b66f8de` (validated) | 1.000089 | 7.181e-05 | 5.235e-02 |
| `8e92c14` (Josh + MR !11) | 1.000089 | 7.181e-05 | 5.235e-02 |

So MR !8/!9's supersession did not move sigma_gen at the anchor. The cache
needs neither a rebuild nor a re-validation of its central values.

### Ancestry is the wrong test on a rebased branch -- check content

Two scares, both false, both from asking `git merge-base --is-ancestor`:

1. **`b66f8de` is not an ancestor of `dce84b1`.** True, and it does not matter:
   MR !8/!9 are closed as superseded (Luca), and `muf_analytic` is absent from
   Josh's head because he *replaced* the approach (the rge-refill /
   frozen-node-FO-refill line), not because it was lost.
2. **`3a8db11` is not an ancestor of `dce84b1`.** Also true, also does not
   matter: that is our MR !7 ("the rule already carries the fixed order --
   stop adding it again"), and `_rule_is_matched` appears **6 times in all
   three** of `b66f8de`, `dce84b1`, `8e92c14`. The content is present; only the
   commit object differs, because Josh's branch is a rebase.

The lesson generalises: for a rebased upstream, an ancestry check answers
"is this commit object in that history", which is not the question. The
question is "is this behaviour present", and only a content or value check
answers it.

### Building it needs a CMake flag the snapshot never needed

Configure dies in the **vendored gtest** (`testing/gtest/CMakeLists.txt:39`):
`cmake_minimum_required` below 3.5, and compatibility with < 3.5 was removed in
CMake 4. Add `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`:

```
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build -j 48
```

The flag only relaxes policy for that vendored subproject. The validated
snapshot predates the container's CMake 4, which is why no earlier build
script carries it.

## Decisions

**Do not quote a muF-direction uncertainty from this library until Josh's
kappa_F note is worked through.** `4179e76` is titled "note on the broken
kappaF mover gradient under rule-replay refill paths" -- rule-replay refill is
our code path, and kappa_F is one of our fit parameters. Josh says
`vars_flag_isolation.py` reproduces his whole anchor-side FD-vs-clad table in
under a minute at 64+ threads, on both `matched_card` and `production_card`,
and that it is "intended for the author to pick up directly". Running that
table is the cheapest way to find out whether it touches us.

Only one of the six commits between `e84f0b3` and `dce84b1` is code
(`4678f44`, "qT/ad: frozen-node FO refill for no-pair caches"); the rest are
docs and probe harnesses.

## Log

**2026-09-08.** Luca asked whether `e84f0b3` was Josh's latest -- it is not,
`dce84b1` is, and `e84f0b3` is its ancestor, so adopting the branch head gets
it for free rather than as a separate decision. Luca then said to adopt Josh's
head + our latest MR, and that MR !8/!9 are closed as superseded, which
removed the objection that had parked this in `260907-adopt-e84f0b3`.
Worktree, build, GlobalData check, central check. Variations running.
