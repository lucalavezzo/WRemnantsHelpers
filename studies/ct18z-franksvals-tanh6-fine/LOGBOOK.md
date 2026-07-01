---
id: ct18z-franksvals-tanh6-fine
title: CT18Z N3+0LL fine SCETlib production at franksvals NP with tanh_6 on both TMD and CS sides
status: running
question: Produce a SCETlib `_combined.pkl` for CT18ZNNLO at N3+0LL with Anton's franksvals NP centrals and variations, but with `np_model = np_model_nu = tanh_6` (lambda6 = 0.016 on TMD, lambda6_nu = 0.0007 hardcoded on CS), so the franks-vals-fit linearization can be cross-checked against an NP shape that includes the tanh_6 lambda_6 terms.
owner: lavezzo
created: 2026-05-21
updated: 2026-05-21
preferred_run: null
tags: [scetlib, ct18z, n3+0ll, tanh_6, franksvals, theory-correction, franks-vals-followup]
parent: franks-vals-fit
investigates_regions: []
investigates_methods: []
investigates_fits: []
investigates_background_estimates: []
investigates_uncertainties: [uncertainty:scetlibNP]
next_action: Monitor cluster 2702601 (2128 jobs, idle as of submission). Watch for hang pattern at var-7 (lambda4=-0.8) analogous to the var-5 (lambda4=-0.4) hang in [[study:ct18z-3p0-newvals-tanh6-lambda6scan]] — lambda4=-0.8 is more extreme so hangs are more likely. Once jobs land, run `combine` op → `_combined.pkl` → downstream chain.
current_hypotheses:
  - Swapping `np_model`/`np_model_nu` from tanh_2 to tanh_6 (with TMD lambda6 default 0.016 and CS lambda6_nu hardcoded 0.0007) on top of Anton's franksvals_fine setup gives a self-consistent NP shape that can be compared head-to-head against his franksvals tanh_2 templates to probe the lambda_6 parametrization freedom on data.
success_criteria:
  - Config dir `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_tanh6_fine` in our scetlib area with the tanh_6 swap applied; user signs off on additional edits before any condor submission.
  - Once submitted: `_combined.pkl` exists, loads, and downstream WRemnants chain consumes it cleanly.
blockers: []
pending_signoffs:
  - User signoff on the rest of the changes ("other things") before building tarball / submitting condor.
---

## Status

2026-05-21 — **Submitted as cluster 2702601, 2128 jobs** (38 vars × 56 bin-steps × 1 PDF, all idle as of submission).

Config at `/work/submit/lavezzo/alphaS/TheoryCorrections/SCETlib/com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_tanh6_fine/`. Diff vs Anton's `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_fine/`:
- `.ini [Nonperturbative]`: `np_model_nu` and `np_model` flipped from `tanh_2` to `tanh_6`; TMD `lambda4` central 0.4 → 0.1; new line `lambda6 = 0.5` (fixed, no variation). Everything else byte-identical (modulo the renamed `.ini`).
- `variations_lattice_allvars.conf`: only `[7]: lambda4 = 0.0 → -0.8` (down). 37 other variation blocks unchanged.
- CS-side: `lambda_6_nu = 0.0007` stays at hardcoded `Gamma_nu.hpp:102` default (no runtime override exists yet).

Submission setup (matches `ct18z-3p0-newvals-tanh6-lambda6scan` family, with `-j 4` per user choice instead of `-j 2`): reused `/ceph/.../scetlib_runtime_submit_ct18z_lambda6.tar.gz` (patched scetlib with runtime `lambda6` exposed); submit dir `/ceph/.../Z_COM13_CT18Z_N3p0LL_NewNPs_Lattice_Lambda4Bugfix_Franksvals_Tanh6_Fine/`; `-b 205 -q workday --max-runtime 28800 --request-disk 2000000 --request-memory-mb 1000`.

**Risk to watch**: var-7 has `lambda4 = -0.8` — more extreme than the var-5 (`lambda4 = -0.4`) variation in the parallel newvals lambda6 study, which **hung every single bin-range** under NCPU=2. With NCPU=4 there is more compute headroom per worker, but a Cuba `max_iterations` saturation behaviour is the dominant failure mode and CPU count won't fix it. Plan: monitor var-7 jobs early — if they hang within ~1h, consider relaxed precision / split bins / a per-bin Cuba override for that variation alone before the workday wall hits.

**Next action**: monitor cluster 2702601; once successful jobs land, run the `combine` op → `_combined.pkl` → downstream chain.

## Guiding Question

Produce a SCETlib `_combined.pkl` for CT18ZNNLO at N3+0LL with Anton's franksvals NP centrals + variations, but with both np_model_nu and np_model set to tanh_6, so franks-vals-fit can compare its tanh_2 linearized data preference against a tanh_6 NP shape with explicit lambda_6 terms in both kernels.

## Hypotheses

- Swapping `np_model`/`np_model_nu` from tanh_2 to tanh_6 (with TMD lambda6 default 0.016 and CS lambda6_nu hardcoded 0.0007) on top of Anton's franksvals_fine setup gives a self-consistent NP shape that can be compared head-to-head against his franksvals tanh_2 templates to probe the lambda_6 parametrization freedom on data. [active]

## Ideas / Methods Explored

- Direct `cp -r` of Anton's `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_fine/` as the cleanest starting point (rather than re-deriving from the newvals lambda6 fine config). The franksvals NP centrals and the wide ±0.4/+0.6 variations on lambda_2 / lambda_4 are the differentiator vs the parallel `ct18z-3p0-newvals-tanh6-lambda6scan` study; preserving them verbatim keeps a clean diff to Anton's existing results.

## Dead-Ends

- (None yet.)

## Findings

- 2026-05-21 — Anton's `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_fine/base.conf` is byte-identical (modulo trailing whitespace) to our existing `com13_ct18z_newnps_n3+0ll_lattice_newvals_lambda6_fine/base.conf` from the parallel study — no calc-settings / TNP differences. Only the `.ini` Nonperturbative block and the variations file differ between configs.
- 2026-05-21 — `lambda6` runtime knob (TMD side) is already plumbed end-to-end via the [[study:ct18z-3p0-newvals-tanh6-lambda6scan]] patch landed in `scetlib-cms-newnp-lambda4fix` (NP_models.hpp:88 + pybind binding + defaults.conf + variations.py). Setting `lambda6 = 0.5` in the new `.ini` therefore exercises the runtime knob ~30x above its hardcoded default. CS-side `lambda_6_nu = 0.0007` remains hardcoded at `Gamma_nu.hpp:102` (not promoted in that patch).
- 2026-05-21 — Anton's actual condor.submit was not accessible (ceph output area cleaned). Submission parameters chosen from the parallel newvals lambda6 production with `-j 4` (user choice) instead of `-j 2`; user explicitly OK'd skipping a local smoke test. Job count: 38 vars × 56 bin-steps × 1 PDF = **2128 jobs** in cluster 2702601 (vs 2408 for the parallel study, since this config has fewer variation entries — 38 vs 43).

## Open Questions

- What "other things" does the user want to change relative to Anton's franksvals_fine setup? Candidate scopes (waiting for user direction): variations-file additions/edits (e.g. extra lambda_4 / lambda_inf excursions like in the parallel newvals lambda6 study, or a CS-side lambda_6 scan if we extend the source patch), grid changes, TNP scope changes, or beamfunc / pdf_set tweaks.
- Will we want a CS-side `lambda_6_nu` runtime knob in scetlib for this run, parallel to the TMD-side patch? Currently CS lambda_6_nu = 0.0007 is fixed by source.
- Downstream chain: scetlib_dyturbo at 3+0 (nnlo_sing companion needed) matching franks-vals-fit input?

## Decisions

- 2026-05-21 — TMD `lambda4` central = 0.1, down variation = -0.8, up variation = 1.0 — reason: user spec; replaces Anton's tanh_2 franksvals central 0.4 with a tanh_6-appropriate central and widens the down direction toward the franks-vals-fit data preference (~-0.78 linearized).
- 2026-05-21 — TMD `lambda_inf` stays at 1.0 — reason: user spec; already matched Anton's franksvals setup, no edit required.
- 2026-05-21 — `lambda6` (TMD) fixed at 0.5, no variation — reason: user spec (after their own calculations); ~30x the prior hardcoded 0.016 default. Requires the `NP_models.hpp:88` runtime patch from `ct18z-3p0-newvals-tanh6-lambda6scan`. No variation block in the .conf because the user did not request a scan here.
- 2026-05-21 — Submitted with `-j 4` (NCPU=4) rather than `-j 2` — reason: user explicit choice when asked. Trades 2× cluster footprint for halved wall-time per job, more headroom against the Cuba `max_iterations` saturation behaviour that hung var-5 jobs in the parallel newvals lambda6 study.
- 2026-05-21 — Skipped a local smoke test before condor submission — reason: user explicit "Please submit". Accepted risk: var-7 (lambda4=-0.8) may hang per the parallel-study precedent at lambda4=-0.4.
- 2026-05-21 — Start from Anton's `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_fine` (not from our existing newvals_lambda6_fine) — reason: user explicitly asked to copy Anton's franksvals setup; keeps a clean tanh_2 → tanh_6 diff against Anton's existing combined.pkl for cross-checks.
- 2026-05-21 — Name the new config dir `com13_ct18z_newnps_n3+0ll_lattice_lambda4bugfix_franksvals_tanh6_fine` (insert `_tanh6` before `_fine`) — reason: matches the convention used by `com13_msht20an3lo_newnps_n3+0ll_lattice_lambda4bugfix_lambda6_lambda6cs_fine` and keeps the lattice/franksvals/fine semantics readable.
- 2026-05-21 — Drop the inherited `_combined.pkl` from the copied dir and rename the `.ini` to match the new dir name — reason: avoid any chance of downstream tooling picking up Anton's tanh_2 output under our tanh_6 directory.
- 2026-05-21 — Add explicit `lambda6 = 0.016` to the TMD `[Nonperturbative]` block — reason: makes the setpoint visible at the config level (so a future `lambda6` scan can land as a one-line variation), even though omitting it would default to the same value via `defaults.conf`.
- 2026-05-21 — Keep `parent: franks-vals-fit` (not `ct18z-3p0-newvals-tanh6-lambda6scan`) — reason: the differentiator vs the existing newvals lambda6 study is the franksvals NP centrals + wide variation set; the work directly extends what franks-vals-fit asked for ("validate the linearized data preference against an explicit non-linear NP shape"), with a different NP-central choice than the sister study.

## Next Action

Confirm with user whether any other changes remain. Then run a local single-bin smoke test (central + at least one lambda4 down/up + one TNP variation) to validate that tanh_6 + lambda4=-0.8 doesn't trigger Cuba convergence failures comparable to the var-5 lambda4=-0.4 hang seen in [[study:ct18z-3p0-newvals-tanh6-lambda6scan]]. Rebuild runtime tarball, prep condor submit. No submission until user signs off.
