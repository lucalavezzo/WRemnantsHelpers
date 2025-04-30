echo "--- WRemnants"
source ../WRemnants/setup.sh
echo
echo "--- WRemnantsHelpers"
export MY_PLOT_DIR="/home/submit/$USER/public_html/alphaS/"
export MY_OUT_DIR="/ceph/submit/data/group/cms/store/user/$USER/alphaS/"
export NANO_DIR="/scratch/submit/cms/wmass/NanoAOD/"
echo "Created environment variable MY_PLOT_DIR=$MY_PLOT_DIR"
echo "Created environment variable MY_OUT_DIR=$MY_OUT_DIR"
echo "Created environment variable NANO_DIR=$NANO_DIR"