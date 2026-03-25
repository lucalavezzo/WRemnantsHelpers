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

## Optional FastJet In Container
- Base image is Arch Linux, and `fastjet` is available through `pacman`.
- Since the `wmassdevrolling` image is immutable on `/cvmfs`, install once into an overlay:
  - `agents/install_fastjet_overlay.sh`
- Launch with the overlay mounted read-only:
  - `agents/run_wmass_with_fastjet.sh`
- Equivalent direct command:
  - `singularity run --bind /scratch/,/work/,/home/,/ceph/ --overlay $HOME/.apptainer/overlays/wmassdevrolling_fastjet.img:ro /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/bendavid/cmswmassdocker/wmassdevrolling\:latest`

## Codex/Container Caveats
- In Codex tool execution, long inline `singularity ... -lc '...'` commands can behave poorly.
- Prefer shorter commands or helper scripts under `agents/`.
- If direct `singularity run ...` fails with `starter-suid doesn't have setuid bit set` in Codex, use approved wrapper launchers (for example `agents/run_wmass_with_heppdt.sh`) with escalated execution.
- Avoid `set -u` in bootstrap scripts that source external setup files.
- If `set -u` is required, bracket setup sourcing with `set +u; source ...; set -u`.
- Frequent failure mode: helper scripts that start with `set -euo pipefail` can exit during `source setup.sh` before any useful output; prefer `set -e` (or disable nounset around sourcing) for environment bootstrap wrappers.

## Last Updated
- 2026-03-04

## Source
- Migration from legacy runtime bootstrap notes (2026-02-16)
- `AGENTS.md`
