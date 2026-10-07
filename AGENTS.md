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
- `studies/<slug>/`: one folder per investigation, holding its `LOGBOOK.md`, its `SUMMARY.md`, its scripts, its outputs, and one subfolder per delegated task.
- `knowledge/`: reference notes that outlive any single study.
- `.claude/`: the agent and skill definitions (`agents/`, `skills/`). Tracked, shared convention — `~/.claude/agents` and `~/.claude/skills` are symlinks to them, so a session finds them from any directory.

Before writing new code, look for something that already does the job: rabbit's own `bin/` tools first, then this repo's `bin/`, `scripts/`, and `workflows/`, and only then something new. Read the `--help` and the existing flags first. New study-specific code goes under `studies/<slug>/`, not in the repo root.

## Logbooks

When you're doing a study, meaning anything past a quick one-off, keep a logbook. There are two layers, and a study looks like this:

```
studies/<study>/
├── LOGBOOK.md          # the orchestrator's record of the study
├── SUMMARY.md (+ .pdf) # the standalone 1-2 page write-up, for people outside the study
├── <YYMMDD>-<task>/    # one directory per delegated task
│   └── LOGBOOK.md      # the worker's record of that task
└── scripts/ QUEUE.md   # study-wide, as before
```

Start a study by copying `studies/_TEMPLATE/LOGBOOK.md`, a task by copying `studies/_TEMPLATE/TASK_LOGBOOK.md`. When you come back to either, read the study's `SUMMARY.md` if it has one, then the "START HERE" block, a short resume block holding the current state, the next step, whatever is blocking, and what's running. As you work, add dated notes under the log, and move anything settled into Findings and Decisions. Before you stop, update "START HERE" and bump `updated:`. That last step is the one that matters, since it's what lets the next session pick up quickly.

**Summaries.** The logbook is the complete record, which makes it hard to read. So each study also gets a `SUMMARY.md`, from `studies/_TEMPLATE/SUMMARY.md`: a standalone one-to-two-page write-up for a member of the analysis who knows the analysis and the code but not this study. It covers why the study was opened and its driving questions, what was done, the findings with their figures and tables, what it changed (code, defaults, cards, `knowledge/`), and the conclusions and open items. It's written at the close of a study, at any major update (a finding that changes the answer, a decision that changes code or defaults, a result going to collaborators), and whenever Luca asks. Never after every task. The `study-summarizer` agent writes it (`/summarize <slug>` dispatches it) and `scripts/summary_pdf.py <slug>` renders `SUMMARY.pdf`; the web viewer opens a study on its summary. The logbook stays the superset: every number in a summary traces to a task logbook. A large task that is really a sub-study can get its own `SUMMARY.md` the same way.

**A task directory is any subdirectory of a study that contains a `LOGBOOK.md`.** That's the rule tools use to find tasks, so never name a task `scripts`, `logs`, `slides`, `docs`, `inputs`, `sessions`, or `__pycache__` — those already exist in study folders for other things.

**Who writes what.** The orchestrator owns `studies/<study>/LOGBOOK.md`; a worker owns its own task directory and writes nothing outside it. When a task finishes, the orchestrator appends one dated line naming the verdict and linking the task logbook — it does not copy the task's numbers up. That is what keeps a study logbook readable (one grew to 300 KB by absorbing every task's detail) and what makes it safe to run several workers at once.

The layers have matching personalities under `.claude/`: the `study` skill for orchestrating (its "Who does what, when" table is the whole lifecycle), and the `study-worker`, `study-summarizer`, `physics-reviewer` and `knowledge-curator` agents.

Nothing enforces this. It's on you, or on Luca telling you, to keep it up.

## Logbooks on the web

Logbooks are browsable at **https://submit.mit.edu/~lavezzo/alphaS/studies/** — `#<study>` for a study, `#<study>/<task>` for a task, and each task page links to its own plot gallery. A study or task with a `SUMMARY.md` opens on the summary, with a Summary / Logbook toggle (`#<study>:logbook` links straight to the logbook), a `pdf` link, and a warning when the logbook has moved past the summary's `covers:` date.

Publish a study once with `scripts/webpublish_study.sh <slug>` (the `study` skill does this for you). It only makes a symlink: there is no build step, so a logbook edit is live on reload and a new task appears as soon as it is created.

**Plots go in the task directory. Not in a separate webdir.** Always `save_plot(outdir=<your task dir>, ...)`, never a hand-rolled `~/public_html/alphaS/YYMMDD_something/`. The reason is the `plots ↗` link on the study page: it points at the task directory, so that is the only place a figure is one click from the logbook entry that explains it. A plot written anywhere else is orphaned from its record and has to be hunted by URL. Group figures into subfolders as freely as you like — the gallery `index.php` lists subdirectories, and `save_plot` writes one into each. This rule is about *figures*: bulk data (caches, `hdf5`, fitresults) still lives on ceph with the path in the logbook.

**Plots can go inline in the logbook too**, wherever a picture says it faster than a paragraph — `![alt](my_plot.png)` from a task logbook, `![alt](<YYMMDD>-<task>/my_plot.png)` from the study logbook. The viewer resolves relative image paths against the logbook's own directory, so a bare relative path just works and an absolute one does not. This is a tool, not a requirement: no logbook needs a figure, and plenty of results are a number or a table. But when a figure *is* the result, embed it rather than leaving a path — keep its caveat next to it, since someone who only looks at the picture must still see it.

Images inside study directories are **not** tracked (see `.gitignore`) — the publish is a symlink to the working tree, so they are live on the web without going into git history. Which means they are not backed up by a push either: keep the script that made them in the task directory, and `save_plot`'s per-plot `.log` records the exact command, so anything lost is one rerun away.

`~/public_html` has **no authentication**, and the symlink publishes everything in the study directory, now and later. So keep bulk outputs on ceph with a path in the logbook, and never put unblinded numbers, credentials, or session transcripts in a study folder. `webpublish_study.sh` refuses a study holding `sessions/`, any `*.jsonl`, or a file over 5 MB until you pass `--force`.

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
- CERN GitLab from this machine (token at `~/.cern_gitlab_pat`, MRs/issues via API or push options): `knowledge/10_environment/cern_gitlab_api.md`
- Nominal workflow and rabbit pitfalls: `knowledge/20_frameworks/nominal_workflow.md`, `knowledge/20_frameworks/profile_likelihood_pitfalls.md`
- Minimizer tolerances, why trust-constr never converges, safe `--earlyStopping`: `knowledge/20_frameworks/rabbit_minimizer_tolerances.md`
- Gen-level (unfolded sigmaUL) fits with the NP param model: `knowledge/20_frameworks/gen_level_sigmaul_fit.md`
- Theory weights and corrections (the histmaker weight formulas): `knowledge/20_frameworks/theory_weights_and_corrections.md`
- Frozen-nominal and validation: `knowledge/20_frameworks/frozen_nominal_spec.md`, `knowledge/20_frameworks/validation_contract.md`
- Histmaker xnorm gen-total drift (+0.240 %, unattributable — never compare gen totals across WRemnants revisions): `knowledge/20_frameworks/histmaker_xnorm_gen_total_drift.md`
- W/Z gen distributions and utilities: `knowledge/20_frameworks/w_z_gen_dists_summary.md`, `knowledge/20_frameworks/utilities.md`
- dokan / NNLOJET production: `knowledge/20_frameworks/dokan_nnlojet.md`
- SCETlib differentiable scales (which are WRONG) and the AD **Jacobian** defects — the clad
  comma-declaration family, and why a derivative must be validated away from the anchor:
  `knowledge/20_frameworks/scetlib_diff_scales_caveats.md`
- What a `--scan` curve does and does not measure, its real cost, and `--scanSaveDetail`:
  `knowledge/20_frameworks/likelihood_scans.md`
- Building an AD cache (which axis parallelises; measured 770-bin stage costs; never cost a build from a high-qT subset): `knowledge/20_frameworks/scetlib_ad_cache_build_parallelism.md`
- Cache format versions and which build may read which cache (TWO incompatible v10s exist): `knowledge/20_frameworks/scetlib_cache_format_versions_and_pins.md`
- Where an AD cache is accurate: exact for `lambda2_nu >= 0`, wrong for `lambda2_nu < 0` (nodes
  placed at the anchor; unwalled fits not trusted), and the qT [0, 0.5] cross-term defect (use
  `merged_full_bin0xzero`), and the MSHT20 mb-threshold staircase in `resumTransition2` (EDM unusable
  for MSHT20 fits floating a transition point): `knowledge/20_frameworks/scetlib_ad_cache_validity.md`
- Saturated and projected-saturated GoF tests: the math, the ndf counting (only exactly-degenerate free
  params reduce a projection's ndf; rabbit does not subtract them), sources: `knowledge/20_frameworks/saturated_gof_tests.md`
- Toy-calibrated saturated GoF tests with a ParamModel + wall (recipe; Wilks holds at the walled
  minimum): `knowledge/20_frameworks/saturated_test_toys.md`
- Several 100-500 GB cache loads on the shared node (`mem_gate.sh`, pause-don't-kill, the
  3-copy stock loader and the uncommitted raw-rules fast path): `knowledge/10_environment/big_memory_jobs.md`
- SCETlib-AD + xFitter, fitting PDFs and alpha_s together (feasibility handoff): `knowledge/20_frameworks/scetlib_ad_xfitter_pdf_fit.md`
- NP parametrization constraints (CS and TMD tanh): `knowledge/30_physics_global/np_parametrization_constraints.md`
- Plotting style and labels: `knowledge/60_plotting_style/plotting_and_labels.md`
- Slide workflow: `knowledge/70_slides/study_slides_workflow.md`
- Glossary: `knowledge/90_glossary.md`
