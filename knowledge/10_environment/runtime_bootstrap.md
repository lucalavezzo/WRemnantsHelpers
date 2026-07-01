# Runtime Bootstrap

## Scope
Container/runtime startup, environment sanity checks, and Codex execution caveats.

## Canonical Facts
- Start environment in this order:
  1. `singularity run --bind /scratch/,/work/,/home/,/ceph/ /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`
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
- 2026-03-04

## Source
- Migration from legacy runtime bootstrap notes (2026-02-16)
- `AGENTS.md`
