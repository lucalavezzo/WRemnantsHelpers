# Runtime Bootstrap

## Scope
Container/runtime startup, environment sanity checks, and Codex execution caveats.

## Canonical Facts
- Start environment in this order:
  1. `singularity run --bind /scratch/,/work/,/home/,/ceph/,/cvmfs/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`
     (`/cvmfs/` in the bind list is not optional if anything will touch LHAPDF or LaTeX -- see "LaTeX in the container" below)
  2. `cd /home/submit/lavezzo/alphaS/WRemnantsHelpers`
  3. `source setup.sh`
- `setup.sh` is the source of truth for `WREM_BASE` and environment variables.
- In this Codex setup, `$WREM_BASE` is inside editable workspace scope.

## Rules I Should Follow
- Never hardcode an assumed WRemnants path; always follow `setup.sh`.
- Verify at session start: `WREM_BASE`, `MY_WORK_DIR`, `MY_PLOT_DIR`, `MY_OUT_DIR`, `NANO_DIR`.
- Use `bin/run --help` as first smoke check.

## Quick Checks
```bash
echo "$WREM_BASE" "$MY_WORK_DIR" "$MY_OUT_DIR" "$NANO_DIR"
which python
python --version
python -c "import hist, ROOT; print('imports_ok')"
bin/run --help
```

## TensorFlow / rabbit venv (verified 2026-04-27)
- Container default Python is 3.14 with no `tensorflow`. The `tensorflow` install lives in `/opt/venv` (Python 3.13).
- Activate the venv inside the container **before** sourcing `setup.sh`, otherwise `import tensorflow` fails and `rabbit_fit.py` will not start. `setup.sh` does not activate it for you.
  - `source /opt/venv/bin/activate`
- `fitter.sh` and other rabbit-driving scripts assume the venv is already active.

## LaTeX in the container (verified 2026-07-29)
- The image has **no TeX at all** — no `pdflatex`, `pdftex`, `latexmk`, `tectonic`. The login node has `/usr/bin/pdflatex`; that one is not reachable from inside.
- `/cvmfs` is **not** visible inside the container with the standard `--bind /scratch/,/work/,/home/,/ceph/` launch: add `/cvmfs/` to the bind list.
  - This is not only a LaTeX nicety: **LHAPDF's sets live there too**
    (`LHAPDF_DATA_PATH=/cvmfs/sft.cern.ch/lcg/external/lhapdfsets/current/:...`,
    set by the container's login profile). Without `/cvmfs/` bound the container
    sees a partial `/cvmfs` in which that directory does not resolve, and
    anything using LHAPDF -- SCETlib in particular -- dies with
    `RuntimeError: Info file not found for PDF set 'CT18ZNNLO'`. The path prints
    correctly in the environment, so the error looks like a missing PDF set
    rather than a missing bind.
  - Two related ways to lose the same thing: `--cleanenv` drops
    `LHAPDF_DATA_PATH` outright, and so does invoking a bare `#!/bin/bash`
    script as the container command -- the variable comes from the LOGIN
    profile, so use `singularity run <img> bash -lc "..."`.
- With it bound, the LCG texlive works in there: `export PATH=/cvmfs/sft.cern.ch/lcg/external/texlive/<year>/bin/x86_64-linux:$PATH` (years 2014–2025 present). Verified compiling `scripts/fit_summary_table.py`'s document.
- Why it matters: it removes the "TF here, pdflatex there" split for scripts that need both — `fit_summary_table.py --compile` finds that pdflatex itself (`find_pdflatex()`: `--pdflatex` / `$PDFLATEX`, then PATH, then newest cvmfs texlive), so one in-container run makes both its TF-dependent NP columns and the pdf.

## Optional Overlays In Container
- Base image is Arch Linux; extra packages can be added through a writable overlay mounted read-only at runtime.
- FastJet:
  - One-time setup: `scripts/overlays/install_fastjet_overlay.sh`
  - Launch: `scripts/overlays/run_wmass_with_fastjet.sh`
- HEPpdt:
  - One-time setup: `scripts/overlays/install_heppdt_overlay.sh`
  - Launch: `scripts/overlays/run_wmass_with_heppdt.sh`
- Equivalent direct command (FastJet example):
  - `singularity run --bind /scratch/,/work/,/home/,/ceph/ --overlay $HOME/.apptainer/overlays/wmassdevrolling_fastjet.img:ro /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`

## Non-Interactive Wrapper Pattern (rabbit / TF jobs)
- Avoid inline `singularity run ... /bin/bash -lc '...long quoted string...'` for multi-step jobs — quoting collisions silently corrupt the command. Write a wrapper script and pass it as the entrypoint.
- **Wrapper scripts live under the relevant study's `scripts/` folder, not in `/tmp/`** — keeps the exact launch script reproducible alongside the study's notes (AGENTS.md study convention). Use `/tmp/` only for short-lived ad hoc debug commands you don't intend to record. Older runlogs reference `/tmp/run_*.sh`; those are historical and should be migrated to `studies/<topic>/scripts/` next time the study is touched.
- Background long-running fits via `nohup singularity run ... studies/<topic>/scripts/<wrapper>.sh > logs/<task>_<timestamp>.log 2>&1 &`. Save the log path immediately so a follow-up monitor can `tail -F` it.
- Working wrapper template:
  ```bash
  #!/bin/bash
  set -e   # NOT -u, see Codex/Container Caveats
  source /opt/venv/bin/activate
  cd /home/submit/lavezzo/alphaS/WRemnantsHelpers
  source setup.sh > /dev/null 2>&1 || true   # || true tolerates harmless echo failures under -e
  rabbit_fit.py "$INFILE" ... -o "$OUTDIR" --freezeParameters mb_up pdfMSHT20mbrangeSymAvg
  echo "DONE_OK $(date)"
  ```
  Launched with:
  ```bash
  nohup singularity run --bind /scratch/,/work/,/home/,/ceph/ \
    /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling:latest \
    /tmp/wrapper.sh > logs/<task>_$(date +%y%m%d_%H%M%S).log 2>&1 &
  ```

## Codex/Container Caveats
- In Codex tool execution, long inline `singularity ... -lc '...'` commands can behave poorly.
- Prefer shorter commands or helper scripts under `scripts/overlays/`.
- If direct `singularity run ...` fails with `starter-suid doesn't have setuid bit set` in Codex, use approved wrapper launchers (for example `scripts/overlays/run_wmass_with_heppdt.sh`) with escalated execution.
- Avoid `set -u` in bootstrap scripts that source external setup files.
- If `set -u` is required, bracket setup sourcing with `set +u; source ...; set -u`.
- Frequent failure mode: helper scripts that start with `set -euo pipefail` can exit during `source setup.sh` before any useful output; prefer `set -e` (or disable nounset around sourcing) for environment bootstrap wrappers.

## Last Updated
- 2026-07-29 (LaTeX in the container / cvmfs texlive)
- 2026-03-04

## Source
- Migration from legacy runtime bootstrap notes (2026-02-16)
- `AGENTS.md`

## `pkill -f` self-matches and kills your own shell

`pkill -f <pattern>` matches the full command line of *every* process, including the
shell running the `pkill` itself and any agent wrapper above it — so a pattern broad
enough to catch your jobs is usually broad enough to catch you. This has cost three
separate sessions now (2026-06 closure fits, 2026-08 branch-switch watcher, 2026-09
branch audit, which lost its shell twice).

Kill by PID after listing, and verify the PID is what you think before signalling:

```bash
pgrep -u "$USER" -f 'prepare_cache_260826' | while read -r p; do
    tr '\0' ' ' < /proc/$p/cmdline | grep -q 'prepare_cache_260826' && kill -TERM "$p"
done
```

Two related traps from the same episodes: a pattern scoped only to a script name can
match **another user's** job (a watcher once matched a colleague's 3.8-day fit and
would have waited forever) — always scope to your own paths and `-u "$USER"`; and
`rabbit_fit.py` installs **no signal handlers** and writes its fitresult only at the
end, so a `kill` discards the run's output entirely, however far along it is.

## Never `git add -A` in WRemnantsHelpers

The repo's `.githooks/pre-commit` runs `black` over **every staged `.py`** and
then re-stages them. So `git add -A` after a day of agent work stages a hundred
freshly written study scripts and reformats the lot in one go — including
copies whose *bytes* carry meaning:

- `studies/<study>/<task>/lib/` — a patched library file shipped ahead of its
  upstream MR, whose md5 the task's `incontainer.sh` prints as provenance
- `studies/<study>/<task>/ab/{A,B}/` — the two arms of an A/B measurement,
  whose whole point is differing by a known handful of lines

Tracked files are recoverable with `git checkout --`; **untracked ones are
not**, and files newly created by an agent in the same session are untracked.
That is how five frozen copies lost their recorded md5 on 2026-09-08.

`pyproject.toml` now carries

```toml
force-exclude = '''
/studies/.*/(lib|ab)/
'''
```

which closes that specific hole. It has to be `force-exclude`: black ignores
`exclude` and `extend-exclude` for paths named **explicitly on the command
line**, which is exactly how the hook passes them, so the pre-existing
`extend-exclude` list never applied to anything the hook touched.

The habit still matters more than the config — commit explicit paths. It also
keeps unrelated in-progress edits (other studies' logbooks, knowledge notes)
out of a commit that claims to be about one thing.

Two related notes: the hook needs `pylint`, which is not installed on the login
node, so a WRemnants commit needs `--no-verify` **plus** the container's
`black`/`isort`/`flake8` run by hand (see `wremnants_ci_linting`). And when a
frozen copy's md5 does drift, the run logs that printed the old hash are the
record of what actually ran — annotate, do not rewrite them.

## Never edit a shell script while an instance of it is running

Bash reads a script **incrementally, by byte offset**, not all at once. Rewrite
the file under a running instance and that instance resumes parsing at its old
offset in the new bytes, so it fails with a syntax error at whatever line now
sits there — or, worse, silently runs a different command than intended.

Seen 2026-09-08: a stage runner was edited to fix one `case` branch while
another branch was mid-run. The running stage finished its real work correctly
(97 variations compared, 99 figures written) and then died with
`syntax error near unexpected token ';;'` pointing at a line it was never
executing, and `Exit status: 2`. The result looked like a failed stage and was
not one.

So: copy the script to a new name and launch that, or wait. And when a
long-running stage reports a syntax error in its own driver, check whether the
driver was edited during the run before believing the stage failed.

Related: the `run_stage.sh` pattern in these study dirs pipes through `grep`
and then reports `rc=$?`, which is **grep's** status, not the command's — so
`STAGE DONE rc=0` says nothing about whether the stage worked. Check
`Exit status:` from `/usr/bin/time -v` in the log instead.
