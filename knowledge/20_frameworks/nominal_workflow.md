# Nominal Workflow

## Scope
Nominal detector-level alphaS chain: histmaker -> rabbit fit -> impacts/FoM.

## Canonical Facts
- Histmaker wrapper: `workflows/histmaker.sh`
- Core histmaker: `${WREM_BASE}/scripts/histmakers/mz_dilepton.py`
- Fitter wrapper: `workflows/fitter.sh`
- Fit setup: `${WREM_BASE}/scripts/rabbit/setupRabbit.py`
- Fit execution: `rabbit_fit.py`
- Impacts plot wrapper: `workflows/pullsAndImpacts.sh`

## Rules I Should Follow
- Launch through `run workflows/<step>.sh` for timestamped logs in `logs/`.
- Prefer `-e "--flag=value"` format for wrapper extra args.
- Use the writer line `Output saved in <path>` as authoritative output location.

## Standard Commands
```bash
run workflows/histmaker.sh
run workflows/fitter.sh <histmaker_hdf5>
workflows/pullsAndImpacts.sh <fitresults_hdf5> -p <tag>
```

Text check equivalent:
```bash
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults_hdf5> --scale 2.0
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults_hdf5> --globalImpacts --scale 2.0
```

## Common Pitfalls
- `-e "--maxFiles 10"` can parse incorrectly; use `-e "--maxFiles=10"`.
- Non-TTY sessions can break naive `tee /dev/tty` usage.
- Grouped nuisance-variation plotting requires fitresult metadata persistence.
  - Ensure `rabbit_fit.py` writes `systs`, `systgroups`, and `systgroupidxs` into `meta`.
  - Then `rabbit_plot_hists.py --varGroupNames <group>` can build on-the-fly grouped bands from `hist_<fitType>_inclusive_variations`.
- **`rabbit_fit.py --freezeParameters` syntax (verified 2026-04-27):** `argparse` is configured with `nargs="+"` (`rabbit/parsing.py:248-251`) — parameters must be **space-separated**, not comma-separated. Comma-separated input becomes a single regex with no matches, so the fit silently runs without freezing anything. Same applies to `--unblind` and other `nargs="+"` flags. Each entry is matched as an exact name *or* a `re.match` (start-anchored) regex; mixing exact and regex entries in a single call is supported (the helper returns the union and de-duplicates). Anchor with `^name$` if you need exact-only.
- **Historical bug fixed 2026-05-01 in `rabbit/fitter.py:match_regexp_params`:** prior to this date the helper used by `--freezeParameters` and `--unblind` returned **only** exact matches whenever *any* entry in the list happened to match a parameter name exactly — silently dropping every regex entry passed alongside it. Symptom: e.g. `--freezeParameters mb_up pdfMSHT20mbrange.*` froze only `mb_up` (regex pass skipped), and the fit then iterated indefinitely because the data wanted `mb_up` to move at ~-1.5σ but it was clamped. To check a suspect fit from before 2026-05-01, grep its log for `Updated list of frozen params` and compare to the input list. Fits run on or after 2026-05-01 use the union of exact + regex matches.
- **POI blinding is a name-seeded constant offset on the NOI central value (αs, mW).** The reported best-fit is `true + offset`, where `offset` is deterministic from the NOI name — so it is **the same across every fit**. Consequences: (1) a large reported pull (e.g. αs postfit ≈ −8.61) is **not a physical location** — the theory prediction is evaluated near the *true* (unknown, ~nominal) value, not at the offset; do **not** inject the reported value as an Asimov truth. (2) **σ is not blinded** — a constant offset shifts the center, not the width — so uncertainty (and correlation) comparisons across fits are directly valid. (3) **Central-value *deltas* between fits are meaningful** (the offset cancels), so you can read how much αs shifted between two fits, but the absolute is hidden until `--unblind`.
- **`setupRabbit.py` defaults to Asimov data — pass `--realData` for a real-data fit (verified 2026-04-27).** Without `--realData`, `data_obs` in the output tensor is the nominal-MC histogram, so even `rabbit_fit.py -t 0` fits the nominal model to itself: prefit chi2 = 0 across every projection, all nuisances at exactly 0 except the NOI, data == prefit prediction bit-for-bit. Only relevant when re-running `setupRabbit.py` yourself; using a pre-built input HDF5 keeps whatever data was written into it.
- **`setupRabbit --presel <axis>:sum lo hi` did NOT cut before WRemnants #736 (merged 2026-10-19):** the bare slice moved
  the content into the flow bins and `hist.sum` re-added it. A card built with `--presel` before then is uncut; rebuild
  it (`studies/ct18z-nominal-fits/261017-wremnants-pr-split` finding 3).
- **Three regex-based per-nuisance overrides (`setupRabbit.py`)**, all matched with `re.search` against the per-direction var name (e.g. `<name>Up`/`<name>Down`):
  - `--scaleParams REGEX=FACTOR` — multiply kfactor (inflate prior). Multiple pairs allowed; overlapping matches raise `ValueError`.
  - `--noSymmetrize REGEX` — keep the systematic asymmetric (don't symmetrize Up/Down).
  - `--noConstrainParams REGEX` — drop the Gaussian prior (free-floating nuisance). Added 2026-05-04, lives in `Datagroups.no_constraint_patterns` and is wired into `addSystematic` next to `scale_params_patterns` / `force_asymmetric_patterns`. Use this instead of patching `rabbit_theory_helper.py:noConstraint=True` lines.
- **Stale `fitresults.hdf5` stubs (verified 2026-06-12):** `rabbit_fit.py` writes the `meta` group at startup and the `results*` group only at the very end — an aborted/killed run leaves a small (~54K) `fitresults.hdf5` containing only `['meta']`. Any later `--externalPostfit` against it fails with the misleading `ValueError: 'results_asimov' not in h5file` (that's just `io_tools.get_fitresult`'s fallback key when `results` is absent — NOT a `-t` mismatch). Naive `[ -f ... ]` existence checks in wrapper scripts pass on the stub; check for a `results*` key or file size when in doubt. `workflows/fitterSCETlibNP.py` (rewritten in python 2026-07-07, replacing the `.sh`) guards against this: before its hessian/saturated steps inherit settings from a fit postfit it checks for a `results*` group and aborts on a meta-only stub. It also keeps `-d/--fitdir <subdir>` to nest fit variants under the datacard dir (and inherits `-t`/`--pseudoData` from the fit postfit in the later steps, `DATA_ARGS` overriding), so multiple fits off one datacard don't trample each other's `fitresults.hdf5`.

## SCETlib-AD fits: the fit and the standard post-fit deliverables (Luca, 2026-10-15)
Every AD (param-model) fit result is shown with the SAME four things, made by the SAME workflow scripts —
never ask, never hand-roll a replacement:

```bash
# fit (one pass: fit + face-held Hessian + traditional/global impacts + hists + ptll saturated projection)
workflows/fitterAD.sh <card> -c <cachedir> -o <out> -p <PF> --constraints [--lattice] -f '<param-model tokens> -v 4'
# 1. pulls + traditional AND global impacts, grouped and ungrouped (POI is alphaS for the param model)
workflows/pullsAndImpacts.sh <out>/fitresults_<PF>.hdf5 -o <taskdir>/impacts -P alphaS
# 2. postfit ptll with the saturated-projection chi2/p (needs --computeSaturatedProjectionTests in the fit)
workflows/plotPtll.sh <out>/fitresults_<PF>.hdf5 -o <taskdir>/ptll
# 3. NP functions: ONE two-panel figure (np_function_plots): CS kernel gamma_nu^NP(b_T) | TMD boundary condition F_eff(b_T,y), fits overlaid with bands
workflows/plotNPFunctions.sh LABEL1=<fitresults1> [LABEL2=<fitresults2> ...] -o <taskdir>/np_functions
# 4. the fit p-value: the full saturated test in the fit log ("Saturated chi2: ndof / 2*deltaNLL / p-value")
```

- `--constraints` = trust-constr with the physical NP region as HARD constraints (`NPDomainConstraints`, margin 0:
  λ2_ν ≥ 0, λ4_ν ≥ 0, L2(Y) ≥ 0 and the cubic, each at |Y| = 0 and 2.5), the default minimisation since 2026-10-15.
  It converges COLD from the anchor, no warm start: all four CT18Z nominal fits (reco/gen × with/without lattice,
  status 1, 46–113 it, 1.6–7.4 h on a loaded node) in `studies/ct18z-nominal-fits/` (261015-cold-tc-fits, 261017-gen-cold-fits);
  first shown in `studies/trust-constr-nominal/261013-constraints-class-validation` (V2).
- `--lattice` adds the ASWZ lattice χ² (`LatticeCSTerm`, defaults = LATFROZ_V3), τ = 8. Since WRemnants cc3859f4 NO
  NP λ carries a prior (TMD and CS), so the lattice is the only external NP information and LAT − NOLAT is exactly the
  lattice term.
- **Never precondition the COLD main fit.** Spectral whitening is built from the Hessian at the start; from the cold
  anchor unit y-steps are ~1σ in soft directions, scipy grows the radius to hundreds, steps get rejected and
  constrained nuisances detour to 11σ. PCLAT (LAT + preconditioner, cold) was ~70× behind LAT in loss at equal wall
  time; no cold main fit was ever faster with it (`ct18z-nominal-fits/261015-trustconstr-precondition`, Log
  2026-10-15 16:10). `fitterAD.sh --constraints` therefore drops `--precondition` for the whole process — which also
  drops it from the saturated sub-fit, where it pays (next bullet).
- **Saturated sub-fits and other warm legs: warm start + full spectral preconditioner** (rabbit #194 merged
  2026-10-19 df99d93: `--precondition` works under trust-constr via the chain rule; #195 `--minimizerWarmStart
  auto|on|off`, READY not merged as of 2026-10-20). Run the post-fit as a SECOND pass from the cold minimum:
  `rabbit_fit.py <card> --externalPostfit <cold fitresults> --noFit <same constraints/lattice/model args>
  --minimizerWarmStart auto --precondition --preconditionParams '.*' --preconditionBlocks none
  --preconditionTransform spectral -m Project ch0 ptll --computeSaturatedProjectionTests --doImpacts --globalImpacts`.
  Templates: `ct18z-nominal-fits/261017-gen-cold-fits/scripts/run_fit.sh` + `run_pf.sh` (gen), `261017-ptll-gof-forensics/scripts/run_p2.sh`
  (warm refit). On LAT's ptll sub-fit: 4667 HVPs / 12.6 h plain (and NOT converged: frozen status 2) → 1504 HVPs
  with the preconditioner alone (3.1×) → 982 HVPs / 3.2 h with both (4.75×), same minimum (q +1.7e-4). The
  preconditioner is the speed; the warm start is correctness (no false stops at releasing faces). Needs a rabbit
  build with #194 + #195 (+ #196 for face impacts): the production `main-plus-ours` tree (2d9f380) has none of them;
  the study used `/work/submit/lavezzo/rabbit-all3`. For a WARM refit (changed card, prior inflation) use
  `--minimizerGtol 1e-5`: a warm leg starts with the barrier already ≤ barrier_tol, its optimality noise floor is
  ~1e-6–1e-5, so gtol 1e-8 only buys a 30–40 % xtol tail at a frozen point (Δloss ≤ 3e-8 at 1e-5;
  `261017-ptll-gof-forensics` Log 2026-10-19). Details: `rabbit_minimizer_tolerances.md`.
- `--externalPostfit <result WITH a covariance> --noFit` does NOT recompute the main Hessian (rabbit `recompute_cov`);
  only a covariance-less input (a snapshot) triggers it (`261016-saturated-subfit-diagnosis` finding 5).
- **Impacts at an active constraint face.** Production rabbit SKIPS `--doImpacts` there (global impacts still run on the
  face-held covariance). rabbit #196 (READY, not merged as of 2026-10-20) computes face-held traditional impacts:
  stat-block covariance from the Lagrangian Hessian on the face directions, groups conditioned on the complement of
  in-group face directions. They equal the fits with the face parameter frozen / eliminated exactly — holding a bound
  face IS freezing that direction, so impacts on a face describe the interval ON it (one-sided if the face binds
  weakly; LAT's released σ(α_s) is ~12 % larger) and need a likelihood scan to be quoted as an interval. Gaussian global
  impacts were already correct; a curved-face correction of the stat remainder was proposed and RETRACTED (the plain
  remainder is exact against the eliminated fit). Evidence: `ct18z-nominal-fits/261016-face-held-impacts`
  (tests/test_face_held_impacts.py, rabbit 1ecae8a). Check the log's `[constraints] active:` lines before reading impacts.
- **A NaN / negative global grouped "Data stat." is not a face effect.** The stat remainder is a difference of
  O(300) terms; when the Hessian minus the priors is indefinite (LAT: −0.022 held) it comes out ≈ 0, negative or NaN.
  Happens with or without faces (`261016-face-held-impacts` finding 3).
- **Gen-level cards cannot go through `fitterAD.sh`** (it hardcodes `-m Project ch0 ptll` and has no
  `--covarianceFit`). Use the two-pass scripts in `ct18z-nominal-fits/261017-gen-cold-fits/scripts/` (`common.sh`,
  `run_fit.sh`, `run_pf.sh`) with `--blindingFrame data`, so gen and reco α_s differences share one blinding offset.
- Run via `mem_gate.sh <GB> <log> -- agent_setup.sh --scetlib <build> -- bash workflows/fitterAD.sh ...`. mem_gate
  re-splits its command with `bash -c "$*"`, so the `-f` value must be single-quoted INSIDE: `-f "'threads=128 -v 4'"`.
- `plotNPFunctions.sh` wraps `scetlib_ad/np_function_plots.py` (WRemnants 74c7e3e3, with an AD-fitresult reader).
  θ → physical λ for a scetlib_ad fitresult needs the card's correction anchor plus `params.REPARAM`;
  `scetlib_np/fitresult_lambdas.py` does NOT do this, `np_function_plots.read_ad_fitresult` does (warns on
  `anchor_override` / `anchor_source=cache`). A fit with a CS λ on its face is drawn central-only unless
  `--band KEY=yes`; toy bands around a point on the curved cubic face run away (not physical). ~40 s for 2–3 fits.
  Validation: `studies/ct18z-nominal-fits/261015-np-functions-tool`.

## Last Updated
- 2026-10-20 (AD section: cold-vs-warm preconditioning, warm-leg post-fit recipe, face-held impacts, gen route; from `studies/ct18z-nominal-fits`)

## Source
- Migration from legacy nominal workflow notes (2026-02-16)
