#!/bin/bash
# Top-level chained launcher for the 260501_debug_1d_yll_vs_4d study.
# Runs the 4D-add-yll-projection refits first (so we have the comparison
# numerator), then the 9 1D yll fits. Sequential to avoid the pthread
# saturation seen on 2026-04-30 18:15.
set +e
SCRIPTS=/home/submit/lavezzo/alphaS/WRemnantsHelpers/studies/260501_debug_1d_yll_vs_4d/scripts
echo "BEGIN_ALL $(date)"
# 1D yll first so the user can start looking at it sooner (~2 min/fit
# vs ~5-10 min/fit for the 4D refits).
echo "=== STAGE 1D-YLL ==="
bash "$SCRIPTS/run_yll_debug_fits.sh"
echo "=== STAGE 4D-ADD-YLL-PROJ ==="
bash "$SCRIPTS/run_4d_add_yll_proj.sh"
echo "DONE_ALL $(date)"
