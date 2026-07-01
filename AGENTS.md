# alphaS analysis — agent guide

This repo (`WRemnantsHelpers`) is the **hub** for the α_s / W-mass analysis: your
own scripts, workflows, per-study logbooks, and durable knowledge. The physics
framework (`WRemnants`) and the analysis documents (`AN-25-085`, `SMP-25-017`)
are **sibling repos**, referenced but not part of this one — see the map below.

> Claude loads this through `CLAUDE.md` (`@AGENTS.md`), and the workspace root
> `../CLAUDE.md` points here too, so any session under `alphaS/` finds it. This
> file is tool-agnostic — keep it readable by any agent (Codex/Copilot included).

## Workspace map

Everything lives side-by-side under the workspace root (`alphaS/`, the parent of
this repo). Reconstruct it with `./clone-siblings.sh`.

| Path | Repo / remote | Role |
|---|---|---|
| `WRemnantsHelpers/` | github `lucalavezzo/WRemnantsHelpers` | **this repo** — the hub (you own it) |
| `main/WRemnants/` | github `origin`=lucalavezzo · `arne`=reimersa · `upstream`=WMass | the physics framework — the canonical checkout |
| `WRemnants-<branch>/` | worktree of `main/WRemnants` | on-demand 2nd branch — make with `wtree` |
| `AN-25-085/` | gitlab `tdr/notes` | **physics ground truth** — the analysis note |
| `SMP-25-017/` | gitlab `tdr/papers` | the public paper |

### Which WRemnants tree / remote
- **One primary checkout: `main/WRemnants`**, carrying three remotes — `origin`
  (your fork), `arne` (reimersa; the shared working branches), `upstream` (WMass).
- Work Arne's shared branches via `arne/<branch>`; PR to `origin` or `arne` as
  appropriate; `upstream` is the true WMass repo.
- **Need a second branch checked out at once?** `wtree <branch>` — a git worktree
  of the primary checkout. Do **not** clone a second copy.

## Setup / runtime

Run inside the WRemnants singularity, activate the venv, then source `setup.sh`:

```bash
singularity run --bind /scratch/,/work/,/home/,/ceph/ \
  /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
source /opt/venv/bin/activate                 # required for rabbit/tensorflow
cd WRemnantsHelpers && source setup.sh        # sets WREM_BASE, MY_*, PATH; regenerates ../CLAUDE.md
```

Key packages: `WRemnants`, `rabbit` (fitting), `wums` (HDF5/plot helpers). Their
sources live under `$WREM_BASE` (resolved by `setup.sh`) — always use that path,
never hardcode.

## Repo layout — where things go

The `bin/` / `scripts/` / `workflows/` / `studies/` split is deliberate; respect it.

| Dir | Holds | Put here when… |
|---|---|---|
| `bin/` | executables on `PATH` (`run`, `wtree`) | it's a reusable command you'll invoke by name |
| `scripts/` | general-purpose tools (plot histmaker output, read fitresults…) | it's useful across many studies |
| `workflows/` | standard recipe chains (histmaker→fit→plot, pulls & impacts…) | it runs the framework end-to-end |
| `studies/<slug>/` | one folder per investigation: `LOGBOOK.md` + `scripts/` + artifacts | it's specific to a single study |
| `knowledge/` | durable cross-study facts (the reference layer) | it's a fact true across the whole analysis |

**Tooling order — before writing new code:** rabbit `bin/` → this repo's `bin/` +
`scripts/` + `workflows/` → only then ad hoc. Read `--help` and existing flags
first. Ad hoc study code belongs in `studies/<slug>/`, not the repo root.

## Logbooks (soft contract)

When you do a study — anything beyond a one-shot lookup — keep a logbook at
`studies/<slug>/LOGBOOK.md` (copy `studies/_TEMPLATE/LOGBOOK.md`; see
`studies/README.md`):

1. **Resuming** → read the **START HERE** block first (current state · next action
   · what's blocking). Don't re-derive what's recorded; don't re-open settled Decisions.
2. **As you work** → append dated bullets under `## Log`; promote durable
   conclusions to `## Findings` and choices to `## Decisions`.
3. **Before ending** → refresh **START HERE** and bump `updated:`. This is the one
   non-optional step; it's what makes the next session cheap.

This is a *soft* contract — enforced by the user directing you to keep it, not by
hooks. Honor it anyway.

## Three durable stores (don't confuse them)

Two live in the repo and are the source of truth; one is Claude's private cache.

| Store | Holds | One-liner |
|---|---|---|
| `studies/<slug>/LOGBOOK.md` | per-study narrative: hypothesis → tried → found → decided | *"what we're doing"* |
| `knowledge/` | cross-study durable facts, distilled from finished studies | *"what's true"* |
| Claude memory (`~/.claude/…`) | auto-loaded index + Claude-only quirks | *"where to look"* |

**Rule:** Claude memory never holds an analysis fact that isn't already in the repo
— it only points to it. **When memory and the repo disagree, the repo wins.**
A finding that proves durable across studies gets promoted from a logbook into
`knowledge/`.

## Physics ground truth

The analysis note **`AN-25-085/AN-25-085.tex`** (env `$MY_AN_DIR`) is the physics
ground truth. Cross-check physics claims against it rather than inferring from
code. A distilled digest lives in `knowledge/30_physics_global/an25_085_digest.md`.
Results aren't "done" until a short physics interpretation is recorded in the
study's logbook — not just "ran successfully".

## More detail (in `knowledge/`)

- Environment / container / bootstrap → `knowledge/10_environment/runtime_bootstrap.md`
- Nominal workflow + rabbit pitfalls → `knowledge/20_frameworks/nominal_workflow.md`,
  `knowledge/20_frameworks/profile_likelihood_pitfalls.md`
- Theory weights & corrections (histmaker weight formulas) → `knowledge/20_frameworks/theory_weights_and_corrections.md`
- Frozen-nominal / validation → `knowledge/20_frameworks/{frozen_nominal_spec,validation_contract}.md`
- W/Z gen dists, utilities → `knowledge/20_frameworks/{w_z_gen_dists_summary,utilities}.md`
- dokan / NNLOJET production → `knowledge/20_frameworks/dokan_nnlojet.md`
- NP parametrization constraints (CS + TMD tanh) → `knowledge/30_physics_global/np_parametrization_constraints.md`
- Plotting style / labels → `knowledge/60_plotting_style/plotting_and_labels.md`
- Slide workflow → `knowledge/70_slides/study_slides_workflow.md`
- Glossary → `knowledge/90_glossary.md`
