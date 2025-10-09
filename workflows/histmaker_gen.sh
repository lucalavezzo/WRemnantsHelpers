# Run the histmaker for the gen level distributions of the alphaS analysis

while getopts "p:" opt; do
    case $opt in
        p)
            postfix=$OPTARG
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
output_dir=$MY_OUT_DIR/${current_date}_histmaker_gen/
if [ -n "$postfix" ]; then
    output_dir=${output_dir}_${postfix}/
else
    output_dir=$output_dir/
fi
mkdir -p $output_dir
echo "Output directory: $output_dir"

command="python ${WREM_BASE}scripts/histmakers/w_z_gen_dists.py --dataPath /scratch/submit/cms/wmass/NanoAOD/ -o ${output_dir} -j -1 --maxFiles -1 --filterProcs  ZmumuPostVFP --useUnfoldingBinning"
echo "Executing command: $command"
eval $command