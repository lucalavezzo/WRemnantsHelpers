#!/bin/bash
# clone-siblings.sh — reconstruct the alphaS workspace.
# Clones the sibling repos next to WRemnantsHelpers if they are missing.
# Safe to re-run: existing checkouts are skipped, never modified.
#
# Layout produced (all under the workspace root, the parent of this repo):
#   WRemnantsHelpers/   this repo (the hub)
#   main/WRemnants/     physics framework (origin=your fork, arne=reimersa, upstream=WMass)
#   AN-25-085/          analysis note (physics ground truth)
#   SMP-25-017/         the paper
#
# For an occasional 2nd WRemnants branch, use `wtree <branch>` (a git worktree),
# not a second clone.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"

clone_if_missing() {
    local dir="$1" url="$2"
    if [ -e "$dir" ]; then
        echo "[skip]  $dir already exists"
    else
        echo "[clone] $dir <- $url"
        mkdir -p "$(dirname "$dir")"
        git clone "$url" "$dir"
    fi
}

# --- WRemnants: one primary checkout with three remotes ---
if [ -e main/WRemnants ]; then
    echo "[skip]  main/WRemnants already exists"
else
    echo "[clone] main/WRemnants <- fork (origin) + arne + upstream"
    mkdir -p main
    git clone git@github.com:lucalavezzo/WRemnants.git main/WRemnants
    git -C main/WRemnants remote add arne     git@github.com:reimersa/WRemnants.git 2>/dev/null || true
    git -C main/WRemnants remote add upstream git@github.com:WMass/WRemnants.git    2>/dev/null || true
    git -C main/WRemnants fetch --all
fi

# --- Analysis documents (CMS GitLab) ---
clone_if_missing AN-25-085  ssh://git@gitlab.cern.ch:7999/tdr/notes/AN-25-085.git
clone_if_missing SMP-25-017 ssh://git@gitlab.cern.ch:7999/tdr/papers/SMP-25-017.git

echo
echo "Done. Next: (in the WRemnants singularity) source WRemnantsHelpers/setup.sh"
