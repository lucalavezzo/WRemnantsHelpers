# pulls and impacts for the alphaS analysis fitting to W and Z

if [ -z "$1" ]; then
    echo "Usage: pullsAndImpactsCombined.sh <infile> -o <output_dir> -e <extra_args>"
    exit 1
fi

input_file="$1"
shift

while getopts "o:e:" opt; do
    case $opt in
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra=$OPTARG
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

if [ -n "$output_dir" ]; then
    echo "Output directory: $output_dir"
else
    current_date=$(date +"%y%m%d")
    output_dir=~/public_html/alphaS/$current_date/
    echo "Output directory: $output_dir"
fi
mkdir -p $output_dir

command="rabbit_plot_pulls_and_impacts.py $input_file --poi pdfAlphaS --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 1.5 --showNumbers --oneSidedImpacts --grouping max -o $output_dir --otherExtensions pdf png -n 50 --poi pdfAlphaS --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle Preliminary ${extra}"

echo "Executing command: $command"
eval $command

command="rabbit_plot_pulls_and_impacts.py $input_file --poi pdfAlphaS --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 1.5 --showNumbers --oneSidedImpacts --grouping max -o $output_dir --otherExtensions pdf png -n 50 --poi pdfAlphaS --impactTitle '<i>α</i><sub>S</sub> in 10<sup>-3</sup>' --title CMS --subtitle Preliminary --globalImpacts ${extra}"

echo "Executing command: $command"
eval $command


command="rabbit_plot_pulls_and_impacts.py $input_file --poi massShiftW100MeV --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 100 --showNumbers --oneSidedImpacts --grouping max -o $output_dir --otherExtensions pdf png -n 50 --poi massShiftW100MeV --impactTitle 'Δ<i>m</i><sub>W</sub>' --title CMS --subtitle Preliminary ${extra}"

echo "Executing command: $command"
eval $command

command="rabbit_plot_pulls_and_impacts.py $input_file --poi massShiftW100MeV --config '${WREM_BASE}/utilities/styles/styles.py' --scaleImpacts 100 --showNumbers --oneSidedImpacts --grouping max -o $output_dir --otherExtensions pdf png -n 50 --poi massShiftW100MeV --impactTitle 'Δ<i>m</i><sub>W</sub>' --title CMS --subtitle Preliminary --globalImpacts ${extra}"

echo "Executing command: $command"
eval $command