# Notes for AI assistants

This repo (`WRemnantsHelpers`) is the hub for the analyses done in the main framework (`WRemnants`), such as $\alpha_S$ and $m_W$: our scripts, workflows, per-study logbooks, and reference notes. The framework (`WRemnants`) and the analysis documents (`AN-25-085`, `SMP-25-017`) are sibling repos that live next to this one, not part of it.

Claude reads this through `CLAUDE.md`, which just does `@AGENTS.md`, and the workspace-root `../CLAUDE.md` points here too, so a session started anywhere under `alphaS/` will find it. Keep it plain enough that any agent (Codex included) can read it. The `README.md` covers the same repo for humans; this file adds the parts an agent needs.

## The workspace

Everything sits side by side under `alphaS/`:

```
WRemnants/          # the framework (remotes: origin=your fork, upstream=WMass)
WRemnantsHelpers/   # this repo
AN-25-085/          # the analysis note, the physics reference
SMP-25-017/         # the paper
```

`./clone-siblings.sh` clones whatever is missing.

There is one `WRemnants` checkout with three remotes: `origin` is your fork and `upstream` is WMass. PR to `origin`, and treat `upstream` as the real WMass repo. If you need a second branch checked out at the same time, run `wtree <branch>` instead of cloning again.

## Running things

Work inside the WRemnants singularity, activate the venv, then source `setup.sh`:

```
singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest
source /opt/venv/bin/activate
cd WRemnantsHelpers && source setup.sh
```

`setup.sh` sets `WREM_BASE`, the `MY_*` paths, and `PATH`, and regenerates `../CLAUDE.md`. The `WRemnants`, `rabbit`, and `wums` sources live under `$WREM_BASE`; use that, don't hardcode paths.

## Where things go

The `bin` / `scripts` / `workflows` / `studies` / `knowledge` split is worth keeping to:

- `bin/`: executables on `PATH` (`run`, `wtree`).
- `scripts/`: general-purpose tools; overlay and container helpers under `scripts/overlays/`.
- `workflows/`: the standard recipe chains, like histmaker to fit to plots, or pulls and impacts.
- `studies/<slug>/`: one folder per investigation, holding its `LOGBOOK.md`, its scripts, and its outputs.
- `knowledge/`: reference notes that outlive any single study.

Before writing new code, look for something that already does the job: rabbit's own `bin/` tools first, then this repo's `bin/`, `scripts/`, and `workflows/`, and only then something new. Read the `--help` and the existing flags first. New study-specific code goes under `studies/<slug>/`, not in the repo root.

## Logbooks

When you're doing a study, meaning anything past a quick one-off, keep a logbook at `studies/<slug>/LOGBOOK.md` (copy `studies/_TEMPLATE/LOGBOOK.md` to start one). When you come back to a study, read the "START HERE" block first; it holds the current state, the next step, and whatever is blocking. As you work, add dated notes under the log, and move anything settled into Findings and Decisions. Before you stop, update "START HERE" and bump `updated:`. That last step is the one that matters, since it's what lets the next session pick up quickly.

Nothing enforces this. It's on you, or on Luca telling you, to keep it up.

## Logbooks vs. knowledge vs. memory

Three places hold durable information and it's easy to confuse them:

- `studies/<slug>/LOGBOOK.md` is what we're doing, the narrative of one study.
- `knowledge/` is what's true, the facts that hold across studies.
- Claude's own memory is just an index that points back into the repo.

When a study turns up something that holds generally, write it into `knowledge/`. Keep Claude's memory pointing at the repo rather than copying facts into it, and if memory and the repo ever disagree, the repo wins.

## Physics ground truth

The analysis note, `AN-25-085/AN-25-085.tex` (also `$MY_AN_DIR`), is the physics reference. Check claims against it rather than inferring them from the code. There's a shorter digest at `knowledge/30_physics_global/an25_085_digest.md`. A result isn't done until there's a short physics read of it in the study's logbook, not just "it ran".

## More detail

Most of the framework knowledge lives under `knowledge/`:

- Environment, container, and bootstrap: `knowledge/10_environment/runtime_bootstrap.md`
- Nominal workflow and rabbit pitfalls: `knowledge/20_frameworks/nominal_workflow.md`, `knowledge/20_frameworks/profile_likelihood_pitfalls.md`
- Theory weights and corrections (the histmaker weight formulas): `knowledge/20_frameworks/theory_weights_and_corrections.md`
- Frozen-nominal and validation: `knowledge/20_frameworks/frozen_nominal_spec.md`, `knowledge/20_frameworks/validation_contract.md`
- W/Z gen distributions and utilities: `knowledge/20_frameworks/w_z_gen_dists_summary.md`, `knowledge/20_frameworks/utilities.md`
- dokan / NNLOJET production: `knowledge/20_frameworks/dokan_nnlojet.md`
- NP parametrization constraints (CS and TMD tanh): `knowledge/30_physics_global/np_parametrization_constraints.md`
- Plotting style and labels: `knowledge/60_plotting_style/plotting_and_labels.md`
- Slide workflow: `knowledge/70_slides/study_slides_workflow.md`
- Glossary: `knowledge/90_glossary.md`
