---
title: Reproduce the nominal walled alpha_s fit
slug: 261001-reproduce-nominal
study: walled-multistart-census
status: done        # active | done | paused | abandoned
created: 2026-10-01
updated: 2026-10-01
owner: study-worker
---

# Reproduce the nominal walled alpha_s fit

**Task:** How does a collaborator reproduce the CURRENT nominal alpha_s fit (Card A + ASWZ lattice CS constraint, y35 bin0xzero cache, NPDampingWall margin 0 tau 8) end to end, from the SCETlib AD cache build to the fit, with exact commands, pinned versions and a reference number? Deliverable: `REPRODUCE.md` in this directory.

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-01)

> **[REPRODUCE.md](REPRODUCE.md) is written: the full chain for the nominal (NOMSTIFF), from SCETlib builds and the AD
> cache build (every flag explained, values read back from the cache header) to the fit, with versions, patches and
> reference numbers.** Three steps are re-run and reproduce the production files exactly (step-5 argv vs NOMSTIFF's
> meta_info via rabbit's parser; lattice injection md5-identical; bin0xzero patch CRC-identical). The NLL at NOMSTIFF's
> stored vector has NOT been re-evaluated: the census fits hold the memory.

- **Next action:** when memory frees (census done, ~22:00-24:00), run
  `setsid nohup scripts/validate_step5.sh > logs/validate_step5.out 2>&1 &` and record the two diffs
  (expect |diff| < 1e-10 against 376.6146329237086 and 376.69103432608273); then flip REPRODUCE.md section 5 row 4.
- **Blocking on:** memory (385 GB free, one gated load needs ~460 GB headroom).
- **For the orchestrator:** the OLD guide (260922-reproduce, on the unauthenticated web) prints the blinded `alphaS`
  central value; rabbit's offset is a deterministic function of public code (sha256 of the name + "_data"), so that
  number is effectively unblinded. Consider redacting it.

---

## Log

<!-- Newest first. What was tried, what happened, why — with an evidence path. -->

### 2026-10-01
- 10:40 Cheap (no cache load) validations, all PASS:
  - `scripts/check_step5_argv.py`: `scripts/step5_fit.sh` parsed by rabbit_fit's own parser equals NOMSTIFF's stored
    `meta_info["command"]` in every option except the run-local -o / --postfix / --snapshotFile (`logs/check_step5_argv.log`).
  - Lattice injection re-run (`inject_aswz_cs_prior_theta.py <card A> -o ... --l4zero`): output md5 7664e885... =
    the production card, byte for byte (`logs/reinject_l4zero.log`).
  - bin0xzero patch re-run (`zero_bin0_crossterms.py merged_full/cache.npz`): fo.npy CRC32 2635307314 = the
    bin0xzero cache's fo.npy member; every other zip member CRC-identical to merged_full (`logs/repatch_bin0xzero.log`).
  - Cache header read back (`rules` SCTRULEV v13, `fo` SCETFOGE v14, format 3, n_eig 29, has_as 1, has_muf 0;
    Bin_rule_opts n_train 9, n_hvp 1, scale 0.15, seed 4242, tol 1e-12, resid_target 1e-7).
- Memory: 385 GB available, three census fits at ~327 GB each. A gated step-5 `--noFit` load needs ~310 GB peak +
  the gate's 150 GB margin, so the NLL-at-stored-vector check is NOT run; `scripts/validate_step5.sh` is ready.
- Sources and patches written to `/ceph/.../alphaS/261001_reproduce_patches/` (not web): wall diffs (as run by
  NOMSTIFF, md5 060a9a36; today's default-0 diff, md5 81d32026), fitterAD.sh diff, wums diff, git bundles of the
  unpushed WRemnants df3c30f7 and rabbit 2a59246, the two correction pkls, and a snapshot of the untracked study
  scripts the chain depends on.
- 10:10 Provenance sweep started (in progress). Read the old guide (260922-reproduce), the three cache knowledge notes,
  NOMSTIFF / LATL4ZY35WALLWARM logs and meta_info, the lattice injector (lattice-cs-kernel/260923-lattice-fits),
  the y35 build task (scetlib-ad-param-model/260921-cache-2da973d), the bin0xzero patch (260924-bilin-nons-cut) and
  y35-fit-prep (card A reused, histmaker skipped). Early findings: cache BUILT at scetlib ca15aec (not 2dd978a; 2dd978a
  is the READER); 60 PDF members (has_muf 0), not 62; the fitresult's git_hash/git_diff is WUMS's, not WRemnants';
  `build_scetlib_ad_cache.py --help` crashes (a bare % in a help string).

---

## Result

**Caveats first.** This task reproduces provenance, not physics; no fit was run and no `alphaS` value was read. The
"nominal" is the study-level nominal (Luca, 2026-09-30), not the AN-25-085 nominal: the AN constrains the CS kernel
with three (lambda_inf_nu, lambda2_nu, lambda4_nu) eigenvariations, here it is a 1D lattice term on lambda2_nu at
lambda4_nu = 0. The scale envelope is the model's 3-point (mu_R-only) default, not the AN text's 7-point one.

The deliverable is [REPRODUCE.md](REPRODUCE.md). What it establishes, beyond restating the old guide:

- **Two SCETlib commits, not one.** The y35 cache was BUILT by `ca15aec` (2da973d + MR !13; unpatched 2da973d aborts
  this build) and is READ by `2dd978a`. Read compatibility is measured for exactly those two; the upstream tip
  (`f1780aa`, same version constants) is expected but not measured to read it.
- **The cache, read back:** rules v13 / fo v14 / format 3, 1050 bins, n_eig 29 + alphaS pair = 60 PDF members
  (has_muf 0, despite the "pdf62" name); Bin_rule_opts n_train 9, n_hvp 1, scale 0.15, seed 4242. Built in one
  process at 384 threads in 32.9 h, 79 % of it the FO quadratic form. Not bit-reproducible (TBB): ~3e-5 in sigma at
  the anchor, up to 3e-3 in Jacobians off it.
- **Card A is unchanged for the new cache**; its central correction still comes from the old 260827 cache + b66f8de
  (the y35 correction agrees to 2.3e-5). The lattice card is card A + an external term (lambda2_nu = 0.134549 ±
  0.031275 → theta mu -0.1545, sigma 0.3127).
- **Versions at the fit:** WRemnants `df3c30f7` (unpushed) + the T1 wall diff (md5 060a9a36); rabbit `2a59246`
  (unpushed: upstream 2a64346 + scan-save-detail); container image digest b4198c00…. rabbit's meta_info records only
  the WUMS git state, so these come from the launcher's `[run]` header.
- **Which reference for what:** NOMSTIFF for the minimum (NLL 376.6146329237086, EDM 3.0e-14, sigma(theta_alphaS)
  0.5823); LATL4ZY35WALLWARM (tau 5, margin 5e-3, a different objective) for GoF / impacts / hists (sat 753.39/778,
  ptll projection 80.73/39).

---

## Findings

1. The y35 cache was built by scetlib `ca15aec`, not `2dd978a` (the reader); `PROVENANCE.txt`'s .so md5s are from the
   earlier aborted 2da973d build and do not match the cache-building library (62c2e930…) —
   (evidence: `/work/.../scetlib-ad-2da973d/PROVENANCE.txt`, `.../build/lib/scetlib_qT*.so` mtime 09-21 22:22).
2. The y35 cache has 60 PDF members (58 eig + alphaS pair), has_muf 0 — (evidence: cache header, `logs/` none; the
   260921 logbook's "member 22 of 60").
3. rabbit_fit's `meta_info` git_hash/git_diff is wums's repository state (wums `output_tools.make_meta_info_dict`),
   not rabbit's or WRemnants' — (evidence: NOMSTIFF meta git_hash 29c884d2 = wums HEAD). Generalises: worth a
   knowledge note.
4. `build_scetlib_ad_cache.py --help` crashes on the bare `%` in the `--fork-members` help — (evidence: run in-container
   2026-10-01).
5. `--noHessian` + `--externalPostfit <file with cov>` is refused by `load_fitresult`; use `--noFit --noEDM` for a pure
   evaluation — (evidence: `rabbit/fitter.py` load_fitresult).
6. The lattice injection and the bin0xzero patch are deterministic and reproduce byte/CRC-identically —
   (evidence: `logs/reinject_l4zero.log`, `logs/repatch_bin0xzero.log`).
7. Several scripts on the nominal chain are untracked in git (injector, bin0 patch, 260921 build scripts, mem_gate.sh);
   snapshot at `/ceph/.../261001_reproduce_patches/scripts_snapshot/`.

---

## Open questions

- Pending: the step-5 `--noFit` NLL check (above).
- The old guide's printed blinded `alphaS` value is recoverable to an absolute value from public code (redaction?).
- Should the untracked chain scripts and `df3c30f7` / `2a59246` be pushed, so a collaborator needs no ceph bundle?
- The `--help` crash in `build_scetlib_ad_cache.py` (one-character fix: `%%`).
- Upstream-tip read compatibility with the y35 cache is unmeasured; a `backend_check.py` with an `f1780aa` build would
  settle it (one cache load).
