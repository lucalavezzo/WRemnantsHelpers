import os
from datetime import datetime

cmd_massive = f"python {os.environ['WREM_BASE']}/scripts/histmakers/w_z_gen_dists.py --dataPath '/scratch/submit/cms/wmass/NanoGen/' --maxFiles '-1' --addBottomAxis -o '{os.environ['MY_OUT_DIR']}/{datetime.now().strftime("%y%m%d")}_gen_massiveBottom' --filterProcs Zbb -v 4 --postfix massive"
cmd_massless = f"python {os.environ['WREM_BASE']}/scripts/histmakers/w_z_gen_dists.py --dataPath '/scratch/submit/cms/wmass/NanoAOD/' --maxFiles '1000' --addBottomAxis -o '{os.environ['MY_OUT_DIR']}/{datetime.now().strftime("%y%m%d")}_gen_massiveBottom' --pdf nnpdf31 --filterProcs ZmumuPostVFP -v 4 --postfix massless"

print("Executing commands:")
print(cmd_massive)
os.system(cmd_massive)
print(cmd_massless)
os.system(cmd_massless)
