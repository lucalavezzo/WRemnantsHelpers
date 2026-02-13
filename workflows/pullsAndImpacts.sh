# pulls and impacts for the alphaS analysis

if [ -z "$1" ]; then
    echo "Usage: pullsAndImpacts.sh <infile> -o <output_dir> -e <extra_args> -p <postfix>"
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
    # ensure only one trailing slash before appending postfix
    extra="${extra%} --postfix ${postfix}"
fi

echo "Output directory: $output_dir"
mkdir -p "$output_dir"

command="rabbit_plot_pulls_and_impacts.py $input_file --poi pdfAlphaS --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 2.0 --showNumbers --oneSidedImpacts --grouping min -o $output_dir --otherExtensions pdf png -n 50 --poi pdfAlphaS --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle Preliminary ${extra}"

echo "Executing command: $command"
eval $command

command="rabbit_plot_pulls_and_impacts.py $input_file --poi pdfAlphaS --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 2.0 --showNumbers --oneSidedImpacts --grouping min -o $output_dir --otherExtensions pdf png -n 50 --poi pdfAlphaS --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle Preliminary --globalImpacts ${extra}"

echo "Executing command: $command"
eval $command
