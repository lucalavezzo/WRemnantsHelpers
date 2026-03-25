echo "--- WRemnants"
source ../main/WRemnants/setup.sh
echo
echo "--- WRemnantsHelpers"
export MY_WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MY_PLOT_DIR="/home/submit/$USER/public_html/alphaS/"
export MY_OUT_DIR="/ceph/submit/data/group/cms/store/user/$USER/alphaS/"
# export MY_OUT_DIR="/scratch/submit/cms/alphaS/" # temporary while ceph is down
export MY_AN_DIR="$(dirname "${MY_WORK_DIR}")/AN-25-085/"
export NANO_DIR="/scratch/submit/cms/wmass/NanoAOD/"
export SCRATCH_DIR="/scratch/submit/cms/"
export PATH="$MY_WORK_DIR/bin:$PATH"
alias print_command="python ${WREM_BASE}/scripts/inspect/print_command.py"
echo "Added $MY_WORK_DIR/bin to PATH"
echo "Created environment variable MY_WORK_DIR=$MY_WORK_DIR"
echo "Created environment variable MY_PLOT_DIR=$MY_PLOT_DIR"
echo "Created environment variable MY_OUT_DIR=$MY_OUT_DIR"
echo "Created environment variable MY_AN_DIR=$MY_AN_DIR"
echo "Created environment variable NANO_DIR=$NANO_DIR"
echo "Created environment variable SCRATCH_DIR=$SCRATCH_DIR"
echo "Created alias print_command to 'python ${WREM_BASE}/scripts/inspect/print_command.py'"
echo
echo "--- PySR/Julia"
export PYTHON_JULIAPKG_PROJECT="$HOME/.julia_env"
export JULIA_DEPOT_PATH="$HOME/.julia_depot"
echo "Created environment variable PYTHON_JULIAPKG_PROJECT=$PYTHON_JULIAPKG_PROJECT"
echo "Created environment variable JULIA_DEPOT_PATH=$JULIA_DEPOT_PATH"
if command -v fastjet-config >/dev/null 2>&1; then
    echo "FastJet available: $(fastjet-config --version)"
else
    echo "FastJet not found in this container session."
    echo "Tip: use agents/install_fastjet_overlay.sh once and launch Singularity with --overlay <overlay.img>:ro"
fi
echo
