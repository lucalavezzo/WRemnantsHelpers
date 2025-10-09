# Run the histmaker for mW analysis

while getopts "p:e:" opt; do
    case $opt in
        p)
            postfix=$OPTARG
            ;;
        e)
            extra_args=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

# check if WREM_BASE is set
if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source the setup.sh in WRemnants."
    exit 1
fi
# check if MY_OUT_DIR is set
if [ -z "$MY_OUT_DIR" ]; then
    echo "MY_OUT_DIR is not set. Please source the setup.sh in WRemnantsHelpers."
    exit 1
fi

# create a subdirectory in the output directory with the current date
current_date=$(date +"%y%m%d")
output_dir="${MY_OUT_DIR}/${current_date}_histmakerMW/"
if [ -n "$postfix" ]; then
    output_dir=${output_dir}_${postfix}/
    postfix="--postfix ${postfix}"
else
    output_dir=$output_dir/
    postfix=""
fi
mkdir -p $output_dir
echo "Output directory: $output_dir"

command="python ${WREM_BASE}/scripts/histmakers/mw_with_mu_eta_pt.py --dataPath /scratch/submit/cms/wmass/NanoAOD/ -o $output_dir --maxFiles -1 --poiAsNoi ${extra_args} ${postfix}"
echo "Executing command: $command"
eval $command
