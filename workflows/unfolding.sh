while getopts "i:u:o:e:f:" opt; do
    case $opt in
        i)
            input_file=$OPTARG
            ;;
        u)
            unfolding_input_file=$OPTARG
            ;;
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

# unfolding command
unfolding_setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i $unfolding_input_file -o $output_dir --analysisMode unfolding --poiAsNoi --fitvar 'ptll-yll-cosThetaStarll_quantile-phiStarll_quantile' --genAxes 'ptVGen-absYVGen-helicitySig' --scaleNormXsecHistYields '0.05' --allowNegativeExpectation --realData --systematicType normal"
echo "Executing command: $unfolding_setup_command"
unfolding_setup_command_output=$(eval "$unfolding_setup_command 2>&1" | tee /dev/tty)

# extract the output file name, and the output directory, where we will put the fit results
unfolding_combine_file=$(echo "$unfolding_setup_command_output" | grep -oP '(?<=Write output file ).*')
echo $unfolding_combine_file
unfolding_combine_file=$(echo "$unfolding_combine_file" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Unfolded file: $unfolding_combine_file"
output=$(dirname "$unfolding_combine_file")
echo "Output: $output"
echo


unfolding_command="combinetf2_fit.py ${unfolding_combine_file} -o ${output} --binByBinStatType normal -t -1 --doImpacts --globalImpacts --saveHists --computeHistErrors --computeHistImpacts --computeHistCov -m Select ch0_masked --postfix asimov ${extra_fit}"
echo "Executing command: $unfolding_command"
unfolding_command_output=$(eval "$unfolding_command 2>&1" | tee /dev/tty)
echo

# extract the output file name, and the output directory, where we will put the fit results
unfolding_fitresult=$(echo "$unfolding_command_output" | grep -oP '(?<=Results written in file ).*')
unfolding_fitresult=$(echo "$unfolding_fitresult" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g') # sanitize the output
echo "Unfolded fit result: $unfolding_fitresult"
output=$(dirname "$unfolding_fitresult")
echo "Output: $output"
echo

setup_command="python $WREM_BASE/scripts/combine/setupCombine.py -i $input_file -o ${output} --fitresult ${unfolding_fitresult} 'Select' ch0_masked --fitvar ptVGen-absYVGen-helicitySig --fitAlphaS --postfix theoryfit --baseName prefsr"
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

combine_command="combinetf2_fit.py ${combine_file} -o ${output} --doImpacts --globalImpacts --saveHists --computeHistErrors --computeVariations --chisqFit --externalCovariance -t -1 -m Basemodel -m Project ch0 ptVGen -m Project ch0 absYVGen ${extra_fit}"
echo "Executing command: $combine_command"
combine_command_output=$(eval "$combine_command 2>&1" | tee /dev/tty)
echo