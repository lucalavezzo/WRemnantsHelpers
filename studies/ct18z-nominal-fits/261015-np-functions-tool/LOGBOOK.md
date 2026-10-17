---
title: NP-function plot for scetlib_ad fits (port of np_function_plots)
slug: 261015-np-functions-tool
study: ct18z-nominal-fits
status: done          # active | done | paused | abandoned
created: 2026-10-15
updated: 2026-10-15
owner: study-worker
---

# NP-function plot for scetlib_ad fits (port of np_function_plots)

**Task:** Can the NP-function figures of `lattice-cs-kernel/261008-np-function-figures` be produced for ANY set of scetlib_ad fitresults by one reusable command, reproducing the 261008 figures exactly?

<!-- Written for a physicist who was not in the session that produced it — this page is
     served on the web. Keep it short; link evidence rather than pasting it. -->

---

## START HERE (status as of 2026-10-15, final scope) — DONE

- **Answer:** The NP-function plot is now the EXISTING scetlib_np plotter (`np_function_plots.py`, branch
  `scetlib-np-param-model`), ported onto the analysis tree as `wremnants/postprocessing/scetlib_ad/np_function_plots.py`
  with a scetlib_ad fitresults reader. It makes ONE figure with two panels, γ_ν^NP(b_T) and F_eff(b_T, y), with the
  num and den fits overlaid with bands.
  - Command: `workflows/plotNPFunctions.sh [LABEL=]<fitresults_A> [[LABEL=]<fitresults_B>] -o <dir>`, which runs from
    the host or the container, from the main WRemnants tree, with no worktree on PYTHONPATH.
  - At most two fits (num / den), as in the original CLI.
  - Validated on LATFROZ_V3 + XWSTIFF: the central curves equal the earlier values at b_T = 1, 2, 3, 4, 6 GeV⁻¹
    to 1 ulp (max |Δ| = 2.2e-16), and the figure is pixel-identical to the first port (Result §A).
- **The tool built first in this task (`scripts/np_functions/`, the 261008 four-figure set) is DELETED.** Luca
  wants only the two-panel plot, with no parallel tool. §0–§4 below are the record of that tool and its validation.
- **Next action:** none. When NOLAT / LAT finish:
  `workflows/plotNPFunctions.sh NOLAT=<out>/fitresults_NOLAT.hdf5 LAT=<out>/fitresults_LAT.hdf5 -o <task dir>`.
- **Blocking on:** nothing. **Running:** nothing.
- **Uncommitted** (as asked). New in `WRemnants` (branch `scetlib-ad-param-model`, untracked):
  - `wremnants/postprocessing/scetlib_ad/np_function_plots.py`, ONE file of 728 lines: the forms, the AD reader,
    the plot and the CLI (consolidated from 3 files and 2622 lines, Log).

  Rewritten in `WRemnantsHelpers`: `workflows/plotNPFunctions.sh`. Deleted: `WRemnantsHelpers/scripts/np_functions/`.
  No other file in either tree was touched (the main tree's other uncommitted edits are someone else's).

---

## Log

### 2026-10-15 (consolidation: one file)
- Luca asked why one plotter took 3 files and 2622 lines. Consolidated into `scetlib_ad/np_function_plots.py`
  (728 lines after black); `np_forms.py` and `np_fit_lambdas.py` are deleted.
- **Kept**: the two-panel plot, the colour and shade helpers, the λ tables, the lattice / MAP22 references and
  `save_plot`. These were copied programmatically (AST), with docstrings cut to one line.
- **Rewritten**:
  - the NP functions as ~25 lines of numpy, for the forms an AD fit can carry, i.e. the ones `np_damping_wall`
    supports (tanh_2 / tanh_6 on each side). The formulas and the operation order are those of `btgrid_tf`
    (λ∞-exact arctanh correction on the TMD side);
  - the reader (θ → λ from `np_damping_wall.resolve_wall_inputs` on the fit's card; faces from
    `damping_conditions`; eigh toys);
  - a minimal CLI.
- **Imported, not copied**: the λ sets per form come from `np_damping_wall._TMD_LAMBDAS` / `_CS_LAMBDAS`.
- **Dropped**:
  - the scetlib_np registry, `NPTune` and the `np_tune` machinery;
  - the raw-λ mode, `--*-lambdas`, `--*-np-model` and `--*-cov`;
  - all the other btgrid forms.
- Re-validation, with the container's black + isort + flake8 (CI line) clean:
  - the curves differ from the earlier values by at most **2.2e-16** (one ulp: numpy vs TF libm, not 0 as before);
  - the two-panel PNG is **pixel-identical** to the previous port's;
  - the wrapper is unchanged and works ([two_panel/run_two_panel.out](two_panel/run_two_panel.out)).

### 2026-10-15 (final scope: port np_function_plots, retire the parallel tool)
*(superseded the same day by the consolidation above; kept as the record)*
- Luca: the NP-function plot is the existing `scetlib_np/np_function_plots.py`; do not maintain a parallel tool.
- **What it imports.** The plotter needs:
  - `btgrid_tf.{F_eff_tf, gamma_nu_NP_tf}` and their helpers;
  - `params` (the registry, `NPTune`, the override parsers);
  - `np_tune` (`add_tune_args`, `side_requested`, `normalize_fitresult_args`, `tune_diff`, `tune_labels`);
  - `plot_output.save_plot`, and lazily `fitresult_lambdas` (scetlib_np only).

  None of these exist on the analysis tree, and no scetlib_ad module evaluates the NP forms (SCETlib does it in C++).
  So I ported:
  - **`scetlib_ad/np_forms.py`**: `scetlib_np/params.py` verbatim, minus the reco/gen axis names and
    `bin_sum_matrix`, plus `btgrid_tf.py`'s form-factor section verbatim (lines 33–493, minus the Simpson / Hankel
    reconstruction).
  - **`scetlib_ad/np_function_plots.py`**: the worktree copy, which is 332b7028 plus its uncommitted `--*-cov` raw-λ
    band. Imports are pointed at `np_forms`; the five `np_tune` helpers and `save_plot` / `split_outpath` are copied
    in verbatim; the `fitresult_lambdas` branch is replaced by the AD reader. Layout, colour contract, legend and the
    lattice / MAP22 references are unchanged.
  - **`scetlib_ad/np_fit_lambdas.py`** (new): the AD reader. It is `compute.read_fit` from the retired tool, without
    TF: θ → λ comes from `np_damping_wall.resolve_wall_inputs` on the fit's card (linear map asserted), the active
    faces from `damping_conditions` (reported), and the toys from `multivariate_normal(method="eigh")` on the
    floating λ (face-held / singular safe). It refuses non-AD fits, warns on `anchor_override`, and never touches
    alphaS rows.
- **Why `scetlib_ad/` and not `scetlib_np/`.**
  - On this tree `scetlib_np/` holds only a stale `validation/__pycache__`. A partial copy of that package (half of
    `params`, a third of `btgrid_tf`) would be an add/add conflict on every file when `scetlib-np-param-model` is
    merged.
  - The new reader is AD-specific and belongs next to `np_damping_wall`.
  - The ported plotter docstring records the provenance.
- Lint: the container's black + isort + `flake8 --max-line-length 88` (the CI line) are clean on the three new files.
  This needed two `# noqa: E203` and four line splits on inherited lines. No other file was formatted.
- `workflows/plotNPFunctions.sh`:
  - it is now a thin wrapper in the plotPtll style;
  - args: ≤ 2 fits, `LABEL=PATH` sets `--num-label` / `--den-label`;
  - default `--y 0 2.5` (the fit acceptance; the plotter's own default also has 5.0), overridable with `-e`;
  - it re-enters through `agent_setup.sh` if run outside the env.
- Deleted `scripts/np_functions/`. The run scripts of its validations stay in this directory, marked RETIRED; they
  no longer rerun.
- Validation: [run_two_panel.sh](run_two_panel.sh) → [two_panel/](two_panel/);
  [check_two_panel.py](check_two_panel.py) → [two_panel/check_two_panel.out](two_panel/check_two_panel.out).

### 2026-10-15 (scope update from the orchestrator / Luca)
- Wanted by default: only two 1D figures, the CS kernel NP part and the TMD boundary factor, with the fits overlaid.
  What changed:
  - **Figures and flags.** `plot.py` gained `cs_kernel` and `tmd_bc` (np_function_plots `gamma_nu_curve` /
    `f_eff_curve` on the reader's λ and toys). They are the default; `--all` adds the four 261008 figures;
    `--only {cs,tmd,1,2,3}` selects individual figures; `--map22` overlays MAP22 on `tmd_bc`.
  - **Stage 1 without SCETlib.** `compute.py` now runs the fit reader first. With `--no-lattice` and no `--all`, it
    writes the λ, covariance and toys and exits (reader-only, run under the default container env). Only otherwise
    does it configure SCETlib (gamma-nu-points) and the lattice term.
  - **Stage 2** no longer asks for any SCETlib build.
  - The run scripts of the earlier validations now pass `--all`. All four validations were rerun end-to-end with the
    final code: repro still byte/pixel as in §1; [run_two_plots.sh](run_two_plots.sh) →
    [two_plots/](two_plots/) and [two_plots/no_lattice/](two_plots/no_lattice/) (the latter's
    [compute.log](two_plots/no_lattice/logs/compute.log) shows the default SCETlib env and "reader-only").
  - Values at b_T = 2 GeV⁻¹ in [two_plots/data/cs_tmd_values.json](two_plots/data/cs_tmd_values.json) match the
    261008 table: γ_ζ^NP lattice / joint / Z-only = −0.314 / −0.158 / −0.335; F^NP(Y=0) = 0.098 / 0.39.

### 2026-10-15
- Read the study START HERE + Decisions, the 261008 task logbook and its `compute.py` / `plot.py`.
- Built `WRemnantsHelpers/scripts/np_functions/`:
  - `np_functions.py`: the single entry point (CLI, `--help`). It writes `<out>/data/np_functions_spec.json`, then
    runs stage 1 (`compute.py`) through `agent_setup.sh --scetlib <gamma-nu-points build>` and stage 2 (`plot.py`)
    through `agent_setup.sh --prepend-pythonpath <scetlib-np-param-model worktree>`. Both stages enter the container
    themselves, so it runs from the host. Stage logs go to `<out>/logs/{compute,plot}.log`.
    `--stage plot` redraws from `<out>/data`; with no `--fit` it reuses the previous run's options.
  - `compute.py`: 261008's compute.py with the fit list read from the spec. It reads each fit's card from the
    fitresult's `meta_info.args.filename` (one offline NPDampingWall per card), not a hardcoded card. It resolves the
    per-fit band policy, and its covariance sampling copes with singular matrices. The rng draw order is kept, so the
    261008 set reproduces exactly.
  - `plot.py`: 261008's plot.py with per-fit drawing rules derived from the fit, in place of the `COL` / `LAB` dicts
    and the hand-placed XWSTIFF/NOMSTIFF elements (rules in its docstring and in Result §2).
  - `workflows/plotNPFunctions.sh`: a thin wrapper in the style of `plotPtll.sh` (`<fitresults...> -o -e`).
- Bugs found while validating, both fixed: a `%` in a legend title (`68.3 %`) broke `%`-formatting; and on a
  plot-only rerun, labels reset to keys (fixed by the reuse-previous-spec rule).
- Validation runs, all end-to-end with the final code (each run script sits in this directory):
  - [run_repro_261008.sh](run_repro_261008.sh) → [repro_261008/](repro_261008/), checked by
    [compare_to_261008.py](compare_to_261008.py);
  - [run_two_fits.sh](run_two_fits.sh) → [two_fits/](two_fits/) (through the workflow wrapper, defaults only);
  - [run_constrained_test.sh](run_constrained_test.sh) → [constrained_test/](constrained_test/) (trust-constr fits
    with a face-held cov).
- Blinding check: grepped every json/log in the three output dirs for alpha. The only hits are the "alphaS"
  directory names in paths and the frozen reference 0.1168. No fitted alpha_s is read into anything that is printed
  or stored.

---

## Result

### A. Current: the two-panel NP-function plot ([run_two_panel.sh](run_two_panel.sh))

```
workflows/plotNPFunctions.sh "Z + lattice (LATFROZ V3)=<A>/fitresults_LATFROZ_V3.hdf5" \
    "Z only (XWSTIFF)=<B>/fitresults_XWSTIFF.hdf5" -o <dir>      # [-e "--y 0 2.5 5 --bT-max 6 ..."]
```

![Two-panel NP functions: left the CS kernel γ̃_ν^NP(b_T), right F_eff(b_T, y) at y = 0, 2.5; LATFROZ V3 (num, viridis) and XWSTIFF (den, plasma) postfit solid with 68 % toy bands, prefit λ_central dashed, lattice fit 2506.13874 and MAP22 in grey](two_panel/np_functions.png)

*Caveats (read before the figure):*
- *The CS panel shows γ̃_ν^NP = 2 γ_ζ^NP. Its grey lattice reference is the plotter's own: the 2506.13874 Eq. 3.34
  fit, with a provisional covariance. It is not our ASWZ V3 lattice-only fit.*
- *Bands are 500 Gaussian toys of each fit's stored covariance. Both fits are walled and sit on active faces, which
  the reader reports:*
  - *LATFROZ_V3 on L2(|Y| = 2.5) = 0;*
  - *XWSTIFF on λ2_ν = 0 and on the TMD large-b face at |Y| = 2.5.*
- *There the toys straddle the face, which has two visible effects:*
  - *XWSTIFF's λ4 ≈ −7e-5 toys go negative, and its |Y| = 2.5 F_eff band runs away upward (λ4 < 0 anti-damps).
    That is the walled Hessian crossing the face, not a measurement.*
  - *The XWSTIFF CS band is the walled width.*
- *The retired tool drew XWSTIFF central-only for this reason. The original plotter has no such option, and it was
  kept as is.*
- *The figure uses the plotter's own matplotlib style, not the wums CMS-label frame (layout kept as instructed).*

**Validation.** The ported plotter's central curves (its reader and numpy forms) were compared with the retired tool's
`cs_kernel` / `tmd_bc` values, which came from the SCETlib-side θ map with the same forms:

| | γ_ζ^NP at b_T = 2 GeV⁻¹ | F_eff(y = 0) | F_eff(y = 2.5) |
|---|---|---|---|
| LATFROZ_V3 | −0.157940 | 0.097883 | 0.127754 |
| XWSTIFF | −0.334984 | 0.391134 | 0.622992 |

They agree at all five b_T and in all three functions to max |Δ| = 2.2e-16 (one ulp; the TF version of the port gave 0).
The PNG is pixel-identical between the two ports
([two_panel/check_two_panel.out](two_panel/check_two_panel.out)). The run was in the container from the main tree
with no worktree on PYTHONPATH ([two_panel/run_two_panel.out](two_panel/run_two_panel.out)). alphaS appears in no
output.

### 0–4. Record: the retired `scripts/np_functions/` tool (deleted 2026-10-15)

### 0. Caveats first
- **Same physics content and caveats as 261008** (its Result §0): every γ_ζ curve uses the LATFROZ frozen
  perturbative kernel (α_s(m_Z) = 0.1168, TNPs = 0, λ∞_ν = 2). Only the CS NP λ differ between curves, so these are
  not the kernels "as in the fit". This keeps the figures blinding-safe.
- **Band policy (default `--band auto`).** A fit whose CS λ sits on its ≥ 0 face (value − bound < 1e-5) is drawn
  as a central curve only, because the width the stored cov gives along that face is the wall's or the face's, not
  a measurement. This is the 261008 convention, and it picks out XWSTIFF automatically. `--band KEY=yes` overrides
  it; the legend then says "face-held band".
- **Face-held / singular covariances** (trust-constr + `NPDomainConstraints`, rabbit's constrained postfit) are
  handled. For the γ_ζ band, an exactly-zero-variance λ is held fixed and the rest is factorised by Cholesky, or by
  eigh with negative eigenvalues clipped if Cholesky fails. The full-NP toys use `multivariate_normal(method="eigh")`.
  The ellipses use eigh with `max(w, 0)`. No Cholesky can fail.
- **The θ → λ map is built offline from the fit's card**, so it does not depend on whether the wall was a `-r` term
  in the fit. The fit kind (wall / constraints / free) is read from meta_info and used for labels only. One trap
  remains: the map uses the correction's anchor, so a fit run with `anchor_override=` or `anchor_source=cache` would
  be mis-mapped. compute.py prints a WARNING when it sees either in the fit's `paramModel` args.
- **tanh_2 CS form only** for the kernel figures: a `tanh_6` CS fit stops with a clear message.
- **Fixed figure elements** that are not fit-derived: the PG value (pass it with `--pg KEY=VALUE`; p and z are
  computed for 2 dof), the total-panel note (`--total-note`), and the λ-plane frame. The frame is the 261008 one,
  widened with 8 % padding only if a drawn element would fall outside it.

### 1. Reproduction of 261008 (LATFROZ_V3, XWSTIFF, NOMSTIFF; [run_repro_261008.sh](run_repro_261008.sh))

| output | vs 261008 |
|---|---|
| `np_figs_data.json` (λ, σ, ρ, χ²_lat, k̂1, faces, band widths) | **byte-identical** |
| `np_functions_values.json` (curves at b_T = 1, 2, 3, 4, 6 GeV⁻¹) | **byte-identical** |
| `cs_kernel_vs_lattice.png` | **0 differing pixels** |
| `cs_kernel_full_range.png` | **0 differing pixels** |
| `np_functions.png` | 0.11 % of pixels, all in one F^NP legend entry: "Z only, \|Y\| = …" where 261008 had "Z only (XWSTIFF), \|Y\| = …" |
| `lambda_nu_plane.png` | 0.11 % of pixels, all in one legend entry: NOMSTIFF's "λ4ν=0" where 261008 had "λ4ν = 0" |

Both residual differences are legend strings that 261008 hand-wrote inconsistently between figures. The tool uses
one label (and its short form) per fit everywhere. The npz itself cannot be compared, because 261008's npz is no
longer on disk. Diff maps: [repro_261008/diff/](repro_261008/diff/).

### 2. The N-fit path ([run_two_fits.sh](run_two_fits.sh), through `workflows/plotNPFunctions.sh`, no options)

![λ-plane for LATFROZ_V3 + XWSTIFF from the tool with default options: lattice-only exact Δχ² contours, LATFROZ_V3 Hessian ellipses, XWSTIFF auto-detected on the λ2_ν = 0 wall face (sliver + annotation)](two_fits/lambda_nu_plane.png)

*Caveat: the perturbative part is frozen at α_s = 0.1168 with TNPs = 0, so these are not the in-fit kernels.
XWSTIFF's dashed sliver is its walled Hessian, not a data constraint.*

The numbers are identical to 261008 (LATFROZ_V3 χ²_lat = 15.87, XWSTIFF 36.47). Per-fit rules used for this run
and any N:
- colours follow the CMS palette after the lattice blue (#e42536, #f89c20, #964a8b, …);
- line styles follow the `--fit` order (`-`, `--`, `-.`, …);
- the first banded fit gets a filled band, the others hatched bands, and central-only fits are drawn on top;
- in the λ plane, a fit off its faces gets 68 / 95 % ellipses, a fit on a CS face gets a sliver plus an annotation
  (worded for a walled Hessian or a face-held cov), and a fit with a held CS λ gets a 1D interval;
- the pull panel shows the lattice plus `--pulls` (default: the first fit).

The other figures: [two_fits/](two_fits/).

### 3. Trust-constr fits with face-held covariances ([run_constrained_test.sh](run_constrained_test.sh))
- **P2B** (nominal config, trust-constr, TMD face L2(|Y| = 2.5)) reproduces LATFROZ_V3's CS block to 1e-6
  (λ = (0.03829, 0.01063), σ = (0.03034, 0.00573), χ²_lat = 15.87). This is consistent with
  trust-constr-nominal/261013's finding that the walled and constrained minima coincide.
- **P1B** (on the λ2_ν = 0 face, face-held) has σ(λ2_ν) = 0 exactly, and its 5×5 NP covariance has eigenvalues
  (0, 2e-20, …). It was detected as on-face and labelled "face held". It was then forced to draw its band
  (`--band all=yes`) to exercise the singular path: no failure, no NaN, and the toys show std(λ2_ν) = 0.
- No WARNING was printed: neither fit has an anchor override.

### 4. Default output: the two NP-function figures (LATFROZ_V3 + XWSTIFF, [run_two_plots.sh](run_two_plots.sh))

```
workflows/plotNPFunctions.sh <fitresults_A.hdf5> [<KEY=fitresults_B.hdf5> ...] -o <task dir> \
    [-e "--label 'KEY=Z + lattice' --no-lattice --all --map22 ..."]
```

![γ_ζ^NP(b_T) = ½γ_ν^NP: lattice-only (ASWZ) band as reference, Z + lattice (LATFROZ V3) with its 68 % band, Z only (XWSTIFF) central only (λ2_ν on its face); lattice range shaded](two_plots/cs_kernel.png)

*Caveat: the NP part of the CS kernel only. It does not depend on α_s or on the perturbative kernel, and has
λ∞_ν = 2 in all three. XWSTIFF has λ2_ν on its ≥ 0 wall face, so it has no band (its stored width there is the
wall's). The lattice-only curve turns positive (anti-damping) beyond b_T ≈ 5.6 GeV⁻¹, because its λ4_ν < 0: it is
an extrapolation outside the shaded lattice range.*

![F^NP(b_T, Y) at |Y| = 0 and 2.5 for Z + lattice (LATFROZ V3, 68 % band) and Z only (XWSTIFF, central)](two_plots/tmd_bc.png)

*Caveat: the bands come from the walled Hessian. LATFROZ_V3 sits on the TMD L2(|Y| = 2.5) = 0 face, so its
|Y| = 2.5 band is pinched by the wall, and is not a Gaussian error there.*

The same two figures without the lattice (stage 1 with no SCETlib) are in [two_plots/no_lattice/](two_plots/no_lattice/).
They are the identical curves; only the lattice reference is missing, and the toys are drawn from a different rng
stream. As the figures show, F^NP is the Z-data split (261008 §5.2): Z only puts the damping on the TMD side
(F^NP wider), and Z + lattice puts it on the CS side.

### 5. Physics read
There is no new physics in this task: it is a tooling task, and the figures are the 261008 figures (read in 261008
Result §5). The check that matters physically is that the reader is right for the new fit class.
- A trust-constr / NPDomainConstraints fit (P2B) gives the same physical λ and CS covariance as the walled fit at the
  same minimum (LATFROZ_V3), to 1e-6.
- The θ → λ map does not depend on how the physical region was imposed in the fit.

---

## Findings

0. FINAL: the NP-function plot for scetlib_ad fits is `scetlib_ad/np_function_plots.py` (the ported scetlib_np
   plotter) through `workflows/plotNPFunctions.sh`. Its curves equal the retired tool's exactly — (evidence:
   [two_panel/check_two_panel.out](two_panel/check_two_panel.out)).
1. (retired tool) `scripts/np_functions/np_functions.py` reproduced 261008. On the 261008 fit set its JSON outputs are byte-identical, and two of the four
   figures are pixel-identical, the other two differing only in one legend string each —
   (evidence: [compare_to_261008.py](compare_to_261008.py), [repro_261008/](repro_261008/)).
2. The reader handles trust-constr face-held covariances: exact zero variance, a 2e-20 eigenvalue. A fit with a CS λ
   on its face is auto-detected and drawn central-only unless `--band KEY=yes` —
   (evidence: [constrained_test/logs/compute.log](constrained_test/logs/compute.log)).
3. The whole chain, stage 1 included, takes ~40 s for 2–3 fits: no cache load and only small SCETlib kernel
   evaluations, and none at all with `--no-lattice` (stage 1 is then only the fitresult reader). It is cheap enough to run after every fit — (evidence: [run_repro_261008.out](run_repro_261008.out)).
4. A worth-knowing caveat for `knowledge/`: θ → physical λ for scetlib_ad fitresults must come from the card's
   correction anchor plus `params.REPARAM`. `fitresult_lambdas.py` (scetlib_np) does not do this; `scetlib_ad/np_function_plots.read_ad_fitresult` does, and it warns on `anchor_override` / `anchor_source=cache`.

---

## Open questions

- The L2(Y) figure (261008 §4, not remade there either) is not part of the tool. It would need only the TMD λ
  already in `data/np_figs_data.npz`.
- The CS-factor panel still uses the canonical rapidity log, not SCETlib's ν_S profile (as in 261008).
- PG tension is passed in, not computed: computing it would need the Z-only fit with its ν priors removed. It is
  out of scope for a plotting tool.
- `scetlib_np/fitresult_lambdas.py` could adopt `compute.read_fit` so that there is a single scetlib_ad-aware λ
  reader.
