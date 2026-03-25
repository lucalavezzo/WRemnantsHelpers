# Perform the unfolding with all the helicity xsecs in ptll-yll-cosThetaStarll-phiStarll
# The fit for alphaS is performed only on the sigma UL in ptVgen-absYVgen using the same MC events

if [ -z "$1" ]; then
    echo "Usage: unfolding_2D.sh <input_file_Z> <input_file_W> <unfolding_fitresult> -o <output_dir> -e <extra setupRabbit arguments> -f <extra rabbit_fit arguments>"
    exit 1
fi

input_file_Z="$1"
input_file_W="$2"
unfolding_fitresult="$3"
shift 3

while getopts "u:o:e:f:" opt; do
    case $opt in
        o)
            output_dir=$OPTARG
            ;;
        e)
            extra_setup=$OPTARG
            ;;
        f)
            extra_fit=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [ -z "$output_dir" ]; then
    output_dir=$(dirname $unfolding_fitresult)
    echo "Set output directory to: $output_dir"
fi

setup_command="python ${WREM_BASE}/scripts/rabbit/setupRabbit.py -i ${input_file_W} ${input_file_Z} -o $(dirname ${unfolding_fitresult}) --fitresult ${unfolding_fitresult} CompositeMapping --fitvar absEtaGen-ptGen-qGen ptVGen-absYVGen --select 'helicitySig -1.0j 0.0j sum' --noi alphaS wmass --postfix CombinedTheoryFitViaMC --baseName prefsr --npUnc LatticeEigvars --pdfUncFromCorr ${extra_setup}"
echo "Executing command: $setup_command"
setup_command_output=$(eval "$setup_command 2>&1" | tee /dev/tty)
echo

# extract the output file name, and the output directory, where we will put the fit results
combine_file=$(echo "$setup_command_output" | grep -oP '(?<=Write output file ).*')
combine_file=$(echo "$combine_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Combine file: $combine_file"
output=$(dirname "$combine_file")
echo "Output: $output"
echo

combine_command="rabbit_fit.py ${combine_file} -o ${output} --doImpacts --globalImpacts --saveHists --computeHistErrors --computeVariations --covarianceFit -t -1 -m BaseMapping -m Project ch1 ptVGen -m Project ch1 absYVGen ${extra_fit}"
echo "Executing command: $combine_command"
combine_command_output=$(eval "$combine_command 2>&1" | tee /dev/tty)
echo