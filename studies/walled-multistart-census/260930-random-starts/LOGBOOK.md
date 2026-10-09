---
title: Random physical start vectors
slug: 260930-random-starts
study: walled-multistart-census
status: done        # active | done | paused | abandoned
created: 2026-09-30
updated: 2026-09-30
owner: study-worker
---

# Random physical start vectors

**Task:** Can we generate randomised, physically-feasible starting vectors around a reference minimum that rabbit accepts as `--externalPostfit` seeds, so a multi-start census samples other NP minima, without leaking the blinded `alphaS`?

---

## START HERE (status as of 2026-09-30)

> **Yes.** [`scripts/make_random_starts.py`](scripts/make_random_starts.py) writes seeds in rabbit's own snapshot format.
> Checks 1-3 pass on every seed: bit-exact round trip through rabbit's real `load_fitresult`, all wall conditions hold at
> margin 0, and no `alphaS` value appears in any output. Check 4 passes too. In the real walled nominal fitter, with the
> reference gate diff = 0.0, the NLL and gradient are finite at every seed tested.
> **Caveat for T4: the starts are FAR from the minimum.** ΔNLL = +277 k (seed 000), +16 k (seed 004), +13.5 k (cold
> start). In the quadratic approximation the s = 2 non-NP kick alone should cost about s²·z·z/2 ≈ 7.7 k. What is
> measured is mostly the data term, and it varies 30× between seeds. This check does not split the NP-draw share from the
> non-NP share. That is fine for a basin census, but convergence will be slow. `--s` and the λ boxes are knobs.

- **Next action:** none. Task closed. T4 uses the script (usage below) and writes its seeds to
  `/ceph/.../alphaS/260930_census_seeds/`.
- **Blocking on:** nothing.

---

## Usage

Run inside the container (`scripts/incontainer.sh` does the singularity, venv and `setup.sh` steps). No cache is loaded.
The card (93 MB) is read once, for the wall's binding |Y|.

```
make_random_starts.py --ref <fitresults.hdf5> --n N --seed S --out <dir>
    [--mode perturb|cold_except_alphas] [--s 2] [--alphas-u 2] [--cold-alphas-u 0]
    [--range lambda2=0,0.5 --range delta_lambda2=-0.03,0.01 --range lambda4=0,0.3
     --range lambda2_nu=0,0.3 --range lambda4_nu=0,0.1] [--margin 0] [--ymax <card>]
    [--prefix seed] [--plot-sample 3000 --plot-dir <taskdir>]
validate_seeds.py --ref <fitresults.hdf5> --dir <dir> --manifest <dir>/manifest_<prefix>.csv
```

Output: `<out>/<prefix>_<k>.hdf5` (about 290 kB each) and `<out>/manifest_<prefix>.csv`. A seed is used as
`rabbit_fit.py ... --externalPostfit <prefix>_<k>.hdf5`.

### How it works (each point checked against the rabbit source, not assumed)

- **Format.** The files are written by `rabbit.snapshot.write_snapshot`, the writer behind the fit's own
  `snapshot_fitresults_*.hdf5`. Each holds the datasets `x` and `parms` (vlen str) and nothing else. `Fitter.load_fitresult`
  (`rabbit/fitter.py:507`) takes its flat branch whenever there is a top-level `x`. It matches by name
  (`np.intersect1d`), so a seed that misses a parameter would silently leave it at x0default. That is why the validator
  requires the parms axis to be identical to the reference's. No `cov` is written: a fit recomputes the Hessian, and a
  seed that carried a `cov` would be loaded into `fitter.cov`. This is the same choice as
  [build_postjump_seed.py](../../alphas-scan-discontinuity/260921-jump-params/scripts/build_postjump_seed.py), which used
  fixed-length `S200` names. Both load identically, since numpy 2's `.astype(str)` decodes bytes.
- **Coordinates.** A fitresult's `parms` histogram is the raw `Fitter.x` (`rabbit_fit.py`: `add_parms_hist(values=ifitter.x)`),
  and so is a snapshot's `x`. The validator confirms this: the nominal `parms` equals its converged snapshot's `x`
  bit-exactly. For a blinded fit this is the **blinded** frame for `alphaS`, because the additive offset is applied inside
  `get_poi` and never to `x`. `load_fitresult` assigns the values raw. So a seed lands in exactly the frame the fit
  minimises in, and no offset is ever touched.
- **Cold start.** `defaultassign()` → `xdefaultassign()` assigns `x0default` raw, in whichever frame is armed. The
  reference's `parms_prefit` is written right after `defaultassign()` and *before* `fit()` loads `--externalPostfit`
  (`rabbit_fit.py:1459-1497` vs `fit()`:794). So `parms_prefit` **is** the cold-start vector, even for a warm fit. For the
  nominal it is all zeros apart from `alphaS` (value not inspected).
- **NP map.** The script uses `W.resolve_wall_inputs(FitInputData(card))`, which is the wall's own resolver on the card
  the reference fit read: forms, anchors, `physical_spec`, and the binding |Y| via `_binding_absY`. It cross-checks the
  result against the fitresult meta chain, the route [physical_lambdas.py](../../alphas-scan-discontinuity/260925-y35zwarm-np-impacts/scripts/physical_lambdas.py)
  uses, and refuses on any mismatch. Nothing is hardcoded.
- **Feasibility.** `W.damping_conditions(..., margin=0)` gives the wall's own `Condition` objects, evaluated with
  `W.numpy_relu2` at |Y| = 0 and at the binding |Y|. The armed/held split mirrors `NPDampingWall.set_expectations`. A
  condition that reads a fitted λ must satisfy value ≥ bound. A condition that reads only held λ is dropped by the wall
  and checked bare (value ≥ 0). Example: λ4_ν ≥ 0 with λ4_ν held at 0, which sits exactly on its face and is legitimate.
- **Random streams.** `SeedSequence(seed).spawn(n)`: seed k depends only on (S, k), not on N. The same S therefore gives
  the same z, u and λ-box draws across references (see the cross-check below).

---

## Log

### 2026-09-30
- Read the flat `load_fitresult` branch, `snapshot.write_snapshot`, `xdefaultassign` and blinding (`get_poi`,
  `set_blinding_offsets`), and the `parms_prefit` write order (evidence: rabbit `2a59246`, lines cited above).
- The wall module `np_damping_wall.py` carries T1's uncommitted `margin=` keyword. It is used here read-only, through
  `damping_conditions(margin=0)` and `_parse_margin`.
- Both references: `cov` is symmetric, has no zero or NaN variances, and the Cholesky of the non-NP block (3714 × 3714)
  succeeds, with eigenvalues from 1.9e-4 to 2.17 (nominal) and 2.1e-4 to 2.13 (cross-check). **The cov is not singular.**
  (evidence: `logs/ref_inspection.log`, `logs/make_seeds_nominal_test.log`)
- Binding |Y| = **2.5** for both references, from `auxiliary[scetlib_np].absYVGen` of their cards. This holds even though
  the cache reaches |Y| = 3.5: the card's gen axis stops at 2.5, and the fit's wall used the same 2.5.
- First draft flagged "λ4_ν ≥ 0" as near-active on every nominal seed. That was wrong: λ4_ν is held at 0 in the nominal,
  so the wall drops that condition. Fixed by mirroring the wall's armed/held logic.
- 10-seed nominal draw (S = 20260930), 1 cold seed, and a 5-seed cross-check draw. All validate
  (evidence: `logs/make_seeds_*.log`, `logs/validate_seeds.log`).
- Blinding grep, with a positive control that detects a planted value (evidence: `logs/blinding_grep.log`,
  `logs/blinding_grep_positive_control.log`). After check 4, the first rerun flagged `logs/seed_nll_check.log`. I located
  the hit with its digits masked: it was a 3-significant-digit rendering of one seed's blinded x, colliding with the
  `ptll` bin-edge printout (`1.5`-style tokens). That is a false positive, and it is not an `alphaS` value. The grep now
  requires at least 4 significant digits, and it passes, with the positive control still detected.
- Check 4: one load gated by `mem_gate.sh` (330 GB, fast raw-rules loader, 188 s). Nothing else was loading, and 1158 GB
  was available. Gate diff 0.0. Finite NLL and gradient at seeds 000, 004 and cold (evidence: `logs/mem_gate.out`,
  `logs/seed_nll_check.log`, `seed_nll_check.json`).
- Skipped a second load (the NP-only vs non-NP-only split of ΔNLL): T2's fits had started loading and only 531 GB was
  available. The variant seeds were deleted. They can be regenerated with the flags given in the Result section.

---

## Result

**Caveats first.** These are start vectors, not fits: nothing here says where a fit started from them will land. All
`alphaS` values are in blinded x and are never shown, and only u is reported. NLL numbers in check 4 are differences to
the reference minimum on real data.

### Validation

| check | what | nominal 10 + cold 1 | cross-check 5 |
|---|---|---|---|
| 1 round trip | loaded through rabbit's real `Fitter.load_fitresult` (unbound, on a stand-in carrying x/parms/cov=None) → equal to the file's x as uint64; names and order identical to the reference `parms` (3719 / 3720); keys exactly `{parms, x}`; `alphaS` == x_ref + u·σ_ref bit-exactly; non-NP displacement whitened with the same L reproduces the manifest's max\|z\| and z·z; cold: every non-`alphaS` entry == `parms_prefit` bit-exactly | PASS 11/11 | PASS 5/5 |
| 2 feasibility | physical λ recomputed from the file's θ via `physical_from_theta`; every armed condition ≥ bound at margin 0; held-only conditions ≥ 0 | PASS 11/11 (closest armed face +0.028, seed 004, λ2_ν) | PASS 5/5 (closest +0.016, seed 002, λ4_ν) |
| 3 blinding | every non-hdf5 file in the task dir (csv, logs, png/pdf bytes, `.log` sidecars, scripts) scanned for the blinded `alphaS` x of both references and all 16 seeds (repr plus f/g renderings with 3-10 decimals and at least 4 significant digits), and for any 0.100-0.135 number on an `alphaS` line. Scripts are scanned for calls that disarm or read offsets; arming with `blind=True`, as the fit itself does, is allowed. A positive control with a planted value is detected (`logs/blinding_grep_positive_control.log`). | 0 / 0 / none | same scan |
| 4 NLL at seeds | walled nominal fitter (see below): finite NLL, finite gradient, wall penalty 0 | PASS 3/3 (000, 004, cold) | not run |

### Check 4: the seeds in the real walled nominal fitter

One gated load, via `mem_gate.sh` at 330 GB. Nothing else was loading, and 1158 GB was available. The cache loaded and
the model was built in 188 s. [`scripts/seed_nll_check.py`](scripts/seed_nll_check.py) rebuilds LATL4ZY35WALLWARM's
Fitter from its own `meta_info` command, minus `-o`, `--snapshot*` and `--externalPostfit`. It uses the default wall at
τ = 5 as in the stored fit, blinding offsets armed and never disarmed. Each seed is then loaded with
`Fitter.load_fitresult`, the `--externalPostfit` path. **Gate:** `reduced_nll` at the reference − stored `nllvalreduced`
= **0.0**. Numbers are differences to the reference minimum (real data, blinded; absolute NLLs are not recorded). Source:
[`seed_nll_check.json`](seed_nll_check.json).

| start | finite NLL / grad | ΔNLL | Δln (data) | Δlc (constraints) | Δlβ (BB stat) | wall pen (τ5 default / margin 0 raw) | max\|∂NLL/∂x\| |
|---|---|---|---|---|---|---|---|
| reference | yes / yes | 0 | 0 | 0 | 0 | 3.2e-3 / 0 | 5.1e-6 |
| seed_000 | yes / yes | +277 265 | +244 929 | +7 797 | +24 529 | 0 / 0 | 9.7e4 |
| seed_004 | yes / yes | +16 357 | +7 779 | +7 601 | +973 | 0 / 0 | 1.3e4 |
| cold_000 | yes / yes | +13 537 | +12 032 | −19 | +1 527 | 0 / 0 | 1.3e4 |

Read: in the quadratic approximation the s = 2 non-NP kick costs ΔNLL ≈ s²·z·z/2 = 7.8 k (seed 000) and 7.7 k (seed 004).
Seed 004's total of 16.4 k is about twice that, so the NP draw plus non-quadratic behaviour add a comparable amount. The
constraint term alone is Δlc ≈ 7.7 k on both seeds. That is the same size as the quadratic estimate, but it does not
reproduce it: the estimate covers the full NLL. The data term is what separates the two seeds. Seed 000 (λ2 = 0.40,
λ2_ν = 0.30, both at the top of their boxes) is 30× further in Δln than seed 004 (λ2_ν = 0.028, close to the reference's
0.063). But seed 000 also has a different z. **This check does not separate the NP draw from the non-NP draw in Δln.**
That would need one more load with NP-only and non-NP-only variants (`--s 0 --alphas-u 0`, `--no-np-draw`). The variants
were built, but the second load was skipped: by then T2's fits were loading and only 531 GB was available. The seed_000
row still shows that a λ box this wide can put a start hundreds of thousands of NLL units uphill. Every start is still
evaluable, with no NaN and no negative yields, and the gradient is finite everywhere.

### 10-seed test draw, nominal (LATL4ZY35WALLWARM, S = 20260930, s = 2, u ∈ [−2, 2])

λ4_ν is not fitted in the nominal (held at its anchor, 0) and is left untouched. No armed face is within 1e-3 of active
on any seed. max\|pull\| is max over non-NP parameters of \|Δx_i\|/σ_i.

| seed | u | λ2 | λ4 | δλ2 | λ2_ν | max\|z\| | max\|pull\| | z·z (n = 3714) | tries |
|---|---|---|---|---|---|---|---|---|---|
| 000 | −0.717 | 0.3985 | 0.0983 | +0.0051 | 0.2986 | 3.90 | 7.81 | 3920 | 1 |
| 001 | −0.264 | 0.0777 | 0.1950 | +0.0048 | 0.1859 | 3.77 | 6.60 | 3689 | 1 |
| 002 | −0.261 | 0.2861 | 0.0474 | −0.0030 | 0.1828 | 3.71 | 7.42 | 3689 | 3 |
| 003 | −1.986 | 0.1917 | 0.0998 | −0.0004 | 0.0461 | 3.56 | 7.15 | 3768 | 1 |
| 004 | −0.454 | 0.1666 | 0.2529 | +0.0062 | 0.0276 | 4.54 | 9.10 | 3837 | 1 |
| 005 | −1.515 | 0.3945 | 0.2312 | −0.0185 | 0.2044 | 3.67 | 7.31 | 3705 | 1 |
| 006 | −1.730 | 0.2427 | 0.2529 | −0.0129 | 0.2038 | 3.74 | 7.48 | 3616 | 1 |
| 007 | +0.002 | 0.3543 | 0.1055 | −0.0167 | 0.2938 | 3.90 | 7.81 | 3715 | 1 |
| 008 | +1.757 | 0.0972 | 0.0154 | −0.0070 | 0.2067 | 3.51 | 7.02 | 3663 | 1 |
| 009 | +0.307 | 0.4948 | 0.0498 | +0.0030 | 0.0946 | 3.80 | 7.60 | 3758 | 2 |
| cold_000 | 0 | 0.4 | 0.4 | 0 | 0.15 | — | — | — | — |

The reference minimum itself is λ2 = 0.0290, λ4 = 0.0873, δλ2 = −0.0039, λ2_ν = 0.0634. The cold start sits at the
anchors, where λ4 = 0.4 lies *outside* the λ4 box [0, 0.3]. It is still physical.

Full-precision manifest: [`seeds_nominal_test/manifest_seed.csv`](seeds_nominal_test/manifest_seed.csv),
[`manifest_cold.csv`](seeds_nominal_test/manifest_cold.csv). Cross-check draw:
[`seeds_crosscheck_test/manifest_seed.csv`](seeds_crosscheck_test/manifest_seed.csv).

![NP λ start draws, nominal: 3000 accepted draws (grey), the 10 written seeds (blue), the reference minimum (red star); physical units; black line = the |Y| = 2.5 small-b face](np_lambda_draws.png)

*Caveat for the figure:* the box is uniform, and the draws are **joint-rejected** only by the wall. Acceptance is 0.865,
and the rejections are almost all on the face L2(|Y| = 2.5) = λ2 + 6.25·δλ2 ≥ 0, the black line. That is why the λ2
marginal is depleted near 0. The reference minimum sits in exactly that corner (λ2 = 0.029, 0.0046 from the |Y| = 2.5
face), so a uniform box puts few starts near it. That is by design, since the census wants other basins. The cross-check
version is [np_lambda_draws_crosscheck.png](np_lambda_draws_crosscheck.png).

### What it means for the census

- The generator does what T4 needs: seeds that rabbit loads unchanged, in the blinded frame, physical by the wall's own
  definition. T4 can pass them with `--externalPostfit` and no other flag changes.
- **s = 2 over 3714 correlated parameters is a big kick.** In the quadratic approximation each perturbed start is
  Δ(NLL) ≈ s²·z·z/2 ≈ 2 × 3714 ≈ 7400 above the reference. Single parameters start up to 9 σ_postfit away, as expected for
  the max of 3714 draws of 2·N(0,1). The fit has to walk all of that back. What that costs in iterations is not measured
  here. If T4 wants the starts to differ *mainly in the NP λ* (the point of the census), s ≈ 0.5-1 would keep the non-NP
  block local. This is a choice for T4, not a defect.
- Seeds for the nominal and the cross-check that share a master seed share their random numbers: the same z, the same u,
  and the same λ-box uniforms until the rejection sequences diverge. Seeds 000, 001, 003 and 004 have identical λ2, λ4,
  δλ2, λ2_ν in both sets. That makes the paired comparison nominal vs cross-check cleaner. Use different `--seed` values
  if independence is wanted.

---

## Findings

1. rabbit's `--externalPostfit` accepts a minimal `{x, parms}` hdf5 written by `rabbit.snapshot.write_snapshot`. It
   matches **by name** and silently leaves any missing parameter at x0default. A seed must therefore carry the full parms
   axis. (evidence: `rabbit/fitter.py:507-533`, `logs/validate_seeds.log`)
2. A fitresult's `parms_prefit` is rabbit's exact cold-start vector (x0default, raw), even for a warm-started fit. It is
   written before `--externalPostfit` is loaded. The nominal's is all zeros apart from `alphaS`. (evidence:
   `rabbit_fit.py:1459-1497`, `manifest_cold.csv` + the validator's bit-exact check)
3. A fitresult's `parms` equals its converged snapshot's `x` bit-exactly. Both are the blinded-frame `Fitter.x`.
   (evidence: `logs/validate_seeds.log`, `[frame]` line)
4. The non-NP postfit cov blocks of both references are PD (min eigenvalue ≈ 2e-4), and the Cholesky works. (evidence:
   `logs/make_seeds_*_test.log`)
5. Binding |Y| for the wall is 2.5 for both references, from the card's `absYVGen`, not the |Y| ≤ 3.5 cache reach.
6. With the default boxes, the wall rejects about 14 % of uniform NP draws, almost entirely on
   λ2 + δλ2·|Y|max² ≥ 0.
7. Random physical NP starts are evaluable in the walled nominal fitter: no NaN, finite gradient. They sit far uphill:
   ΔNLL 1.6e4-2.8e5 at s = 2, and 1.35e4 at the cold start. (evidence: `seed_nll_check.json`)

---

## Open questions

- How many minimiser iterations does an s = 2 start cost compared with s = 0.5? Only T4 can say. Consider running one of
  each first. Starts sit 1e4-3e5 NLL units uphill (check 4).
- How much of Δln at a perturbed seed comes from the NP draw and how much from the non-NP kick? One gated load answers
  it: `--s 0 --alphas-u 0` gives an NP-only seed and `--no-np-draw` a non-NP-only seed, with the same `--seed`.
- Seen in passing, not mine: a `bfs / -name ad_kernel.hpp` crawler (pid 1591358) owned by another session is walking the
  whole filesystem. `knowledge/10_environment/big_memory_jobs.md` warns about exactly this.
- The λ boxes are uniform in the physical λ, not in θ, and not scaled by any posterior width. For λ2_ν, [0, 0.3] is about
  13 σ_postfit wide around a reference at 0.063 ± 0.023. That is intended, since the goal is basin hunting.
