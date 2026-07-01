# WRemnantsHelpers

Scripts, common workflows, studies, and reference notes for the `WRemnants` framework ecosystem: `WRemnants`, `rabbit`, `wums`, `narf`.

We assume you're running in the `WRemnants` singularity:

```
singularity run --bind /scratch/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest
```

To initialize the environment, 

```
source setup.sh
```

Which relies on the sibling repos living next to this one,

```
WRemnants/          # the framework (your fork; remotes origin / arne / upstream)
WRemnantsHelpers/   # this repo
AN-25-085/          # the analysis note
SMP-25-017/         # the paper
```

If any of those are missing, `./clone-siblings.sh` will clone them for you.

## `scripts/`
General-purpose scripts for use with `WRemnants` and `rabbit`, for example, plotting histmaker outputs, opening fitresults, etc.

## `workflows/`
Common recipes for running the framework, such as running the full histmaker-fitter-plotting chain for given analyses, plotting the pulls and impacts for the $\alpha_S$ fits, etc.

## `studies/`
One folder per study, holding everything for that study in one place: its scripts, its outputs, and a `LOGBOOK.md`. Usually more specific, less of general interest, than what is found in `workflows/`.

The `LOGBOOK.md` is the running record of a study. Start a new one by copying `studies/_TEMPLATE/LOGBOOK.md`; the "START HERE" block at the top is meant to be the first thing you read when you pick the study back up. See `studies/README.md` for the details.

## `knowledge/`
Reference notes that aren't tied to a single study. When something we learn in a study turns out to hold generally, it gets written up here.

## `bin/`
Executables added to the `PATH` by `setup.sh`.

- `bin/run`: will run the script in the background, detach the process, and log the output to `logs/my_script_<date>.log`. Usage,
    
    ```
    run scripts/my_script.sh
    ```

- `bin/wtree`: check out a second `WRemnants` branch at the same time, as a git worktree next to `WRemnants/`, instead of a second clone. Usage,

    ```
    wtree new-feature
    ```

## For humans using AI assistants
The setup script creates `AGENTS.md` and `CLAUDE.md` in the parent directory, alongside `WRemnants/`, `WRemnantsHelpers/`, etc.

## For AI assistants
`AGENTS.md` is the guide for agents working in here (Claude, Codex, ...), and `CLAUDE.md` just points at it. If you're an agent, read `AGENTS.md` first.

## Code style
Use [Black](https://black.readthedocs.io/en/stable/) for Python formatting. A lightweight Git hook runs Black on staged Python files before each commit. It is not enforced.

### Enabling the hook
1. Ensure `black` is on `PATH`.
2. Point Git to the repo-provided hooks: `git config core.hooksPath .githooks`

You can always format manually with `black --config pyproject.toml .` if you want to run it yourself.
