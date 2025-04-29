# Run the histmaker for alphaS analysis

current_date=$(date +"%H-%M_%d-%m-%Y")
output_dir=~/cms/alphaS/$current_date/
mkdir -p $output_dir
echo "Output directory: $output_dir"

# check if WREM_BASE is set
if [ -z "$WREM_BASE" ]; then
    echo "WREM_BASE is not set. Please source the setup.sh in WRemnants."
    exit 1
fi

python ${WREM_BASE}/scripts/histmakers/mz_dilepton.py --dataPath /scratch/submit/cms/wmass/NanoAOD/ -o $output_dir --maxFiles -1 --axes ptll yll --csVarsHist --forceDefaultName