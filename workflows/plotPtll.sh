# plot the ptll distribution for the alphaS analysis

if [ -z "$1" ]; then
    echo "Usage: plotPtll.sh <infile> -o <output_dir> -e <extra_args> -p <postfix>"
    exit 1
fi

input_file="$1"
shift

postfix=""

while getopts "o:e:p:" opt; do
    case $opt in
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra=$OPTARG
            ;;
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

if [ -z "$output_dir" ]; then
    current_date=$(date +"%y%m%d")
    output_dir=~/public_html/alphaS/${current_date}_alphaS_pulls_and_impacts/
fi

if [ -n "$postfix" ]; then
    extra="${extra} --postfix ${postfix}"
fi

echo "Output directory: $output_dir"
mkdir -p "$output_dir"

command="rabbit_plot_hists.py $input_file -m 'Project ch0 ptll' --config '${WREM_BASE}/wremnants/utilities/styles/styles.py' --title CMS --titlePos 0 --subtitle Preliminary -o $output_dir --processGrouping 'z_dilepton' --yscale '1.25' --rrange 0.99 1.01 ${extra}"

echo "Executing command: $command"
eval $command
