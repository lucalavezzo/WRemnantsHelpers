import sys

sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/rabbit")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants/wums")
sys.path.insert(0, "/home/submit/lavezzo/alphaS/main/WRemnants")

from rabbit import inputdata, debugdata

hdf5_path = "/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/260409_histmaker_dilepton_unfolding/ZMassDilepton_ptll_yll_cosThetaStarll_quantile_phiStarll_quantile_ISRON/ZMassDilepton.hdf5"

print("Loading input data...")
indata = inputdata.FitInputData(hdf5_path)

print("\nCreating debug data...")
debug = debugdata.FitDebugData(indata)

target_syst = "pythiaew_ISR_Corr0"

print(f"\n=== channelsForNonzeroSysts for {target_syst} ===")
channels = debug.channelsForNonzeroSysts(systs=[target_syst])
if channels:
    for ch in channels:
        print(f"  {ch}")
    print(f"Total: {len(channels)} channels")
else:
    print("  NO channels have nonzero entries for this systematic!")

print(f"\n=== procsForNonzeroSysts for {target_syst} ===")
procs = debug.procsForNonzeroSysts(systs=[target_syst])
if procs:
    for p in procs:
        print(f"  {p}")
else:
    print("  NO processes have nonzero entries!")

# Per channel+process breakdown
print(f"\n=== Detailed breakdown (channel / process) ===")
all_procs = list(debug.axis_procs)
for channel in indata.channel_info:
    for proc in all_procs:
        ch_list = debug.channelsForNonzeroSysts(procs=[proc], systs=[target_syst])
        if channel in ch_list:
            print(f"  {channel} / {proc}: NONZERO")
