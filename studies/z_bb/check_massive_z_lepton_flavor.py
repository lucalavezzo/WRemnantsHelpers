import argparse

import ROOT
from wremnants.datasets.dataset_tools import getDatasets


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check Z-decay lepton flavors (LHE final state) in massive Zbb sample."
    )
    parser.add_argument("--dataPath", default="/scratch/submit/cms/wmass/NanoAOD/")
    parser.add_argument("--era", default="13TeVGen")
    parser.add_argument("--maxFiles", type=int, default=20)
    parser.add_argument("--filterProc", default="Zbb_MiNNLO")
    return parser.parse_args()


def dataset_files(dataset):
    for attr in ["filepaths", "files", "filenames"]:
        if hasattr(dataset, attr):
            val = getattr(dataset, attr)
            if val:
                return list(val)
    raise RuntimeError(f"Could not find file list on dataset object for {dataset.name}")


def main():
    args = parse_args()

    datasets = getDatasets(
        maxFiles=args.maxFiles,
        filt=[args.filterProc],
        excl=[],
        extended=True,
        nanoVersion="v9",
        base_path=args.dataPath,
        era=args.era,
    )

    if not datasets:
        raise RuntimeError(f"No datasets matched filterProc={args.filterProc}")

    print(f"Matched datasets: {[d.name for d in datasets]}")

    total_events = 0
    mu_only = 0
    e_only = 0
    tau_only = 0
    mixed_or_other = 0

    for ds in datasets:
        files = dataset_files(ds)
        print(f"\nDataset: {ds.name}")
        print(f"Files used: {len(files)}")

        df = ROOT.RDataFrame("Events", files)
        df = df.Define(
            "n_lhe_e", "Sum((LHEPart_status == 1) && (abs(LHEPart_pdgId) == 11))"
        )
        df = df.Define(
            "n_lhe_mu", "Sum((LHEPart_status == 1) && (abs(LHEPart_pdgId) == 13))"
        )
        df = df.Define(
            "n_lhe_tau", "Sum((LHEPart_status == 1) && (abs(LHEPart_pdgId) == 15))"
        )

        n_evt = int(df.Count().GetValue())
        n_mu_only = int(
            df.Filter("n_lhe_mu == 2 && n_lhe_e == 0 && n_lhe_tau == 0")
            .Count()
            .GetValue()
        )
        n_e_only = int(
            df.Filter("n_lhe_e == 2 && n_lhe_mu == 0 && n_lhe_tau == 0")
            .Count()
            .GetValue()
        )
        n_tau_only = int(
            df.Filter("n_lhe_tau == 2 && n_lhe_e == 0 && n_lhe_mu == 0")
            .Count()
            .GetValue()
        )
        n_mixed_other = n_evt - n_mu_only - n_e_only - n_tau_only

        total_events += n_evt
        mu_only += n_mu_only
        e_only += n_e_only
        tau_only += n_tau_only
        mixed_or_other += n_mixed_other

        print(f"Events: {n_evt}")
        print(f"  mu-only (2 mu): {n_mu_only}")
        print(f"  e-only  (2 e):  {n_e_only}")
        print(f"  tau-only(2 tau): {n_tau_only}")
        print(f"  mixed/other: {n_mixed_other}")

    print("\n=== Combined summary ===")
    print(f"Total events: {total_events}")
    if total_events > 0:
        print(f"mu-only fraction: {mu_only/total_events:.6f}")
        print(f"e-only fraction: {e_only/total_events:.6f}")
        print(f"tau-only fraction: {tau_only/total_events:.6f}")
        print(f"mixed/other fraction: {mixed_or_other/total_events:.6f}")


if __name__ == "__main__":
    main()
