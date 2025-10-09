
uncerts=(
  "eff*"
  "WidthW0p6MeV"
  "Sin2thetaZ0p00003"
  "pdfAlphaSByHelicity"
  "scetlib*"
  "resum*"
  "QCD*"
  "helicity_shower_kt"
  "pdf*"
  "massWeightZ"
  "renesanceEWCorr"
  "ew*"
  "horace*"
  "pythiaew_ISRCorr"
  "lumi"
  "CMS_*"
  "Fake*"
  "muon*"
  "pixelMultiplicitySyst"
)

for uncert in "${uncerts[@]}"; do
  /home/submit/lavezzo/alphaS/WRemnantsHelpers/scripts/breitwigner/test_syst_exclusion.sh "$uncert"
done