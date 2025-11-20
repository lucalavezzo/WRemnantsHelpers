# Run the histmaker for alphaS analysis

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
output_dir="${MY_OUT_DIR}/${current_date}_histmaker_dilepton/"
if [ -n "$postfix" ]; then
    postfix="--postfix ${postfix}"
else
    postfix=""
fi
mkdir -p $output_dir
echo "Output directory: $output_dir"

command="python ${WREM_BASE}/scripts/histmakers/mz_dilepton.py --dataPath /scratch/submit/cms/wmass/NanoAOD/ -o $output_dir --maxFiles -1 --axes ptll yll --csVarsHist --forceDefaultName ${extra_args} ${postfix}"
echo "Executing command: $command"
eval $command
