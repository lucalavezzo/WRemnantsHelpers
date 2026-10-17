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

- `--constraints` = trust-constr with the physical NP region as HARD constraints (`NPDomainConstraints`), the
  default minimisation since 2026-10-15 (converges from the cold anchor; V2 in
  `studies/trust-constr-nominal/261013-constraints-class-validation`). It turns OFF the spectral preconditioner:
  rabbit refuses `--precondition` with trust-constr (the constraint Jacobian/HVP are not transformed to the
  preconditioned coordinates — an implementation gap, not a limitation of the method).
- `--lattice` adds the ASWZ lattice χ² (`LatticeCSTerm`, defaults = LATFROZ_V3), τ = 8. Since WRemnants cc3859f4 NO
  NP λ carries a prior (TMD and CS), so the lattice is the only external NP information.
- At an ACTIVE constraint face rabbit SKIPS `--doImpacts` (global impacts still run on the face-held covariance; the
  grouped `stat` remainder can be NaN). Check the log's `[constraints] active:` lines before reading impacts.
- Run via `mem_gate.sh <GB> <log> -- agent_setup.sh --scetlib <build> -- bash workflows/fitterAD.sh ...`. mem_gate
  re-splits its command with `bash -c "$*"`, so the `-f` value must be single-quoted INSIDE: `-f "'threads=128 -v 4'"`.
- `plotNPFunctions.sh` wraps `np_function_plots.py` (ported to the analysis branch 2026-10-15, with an AD-fitresult reader).
  Validation: `studies/ct18z-nominal-fits/261015-np-functions-tool`.

## Last Updated
- 2026-10-15

## Source
- Migration from legacy nominal workflow notes (2026-02-16)
