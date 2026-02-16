# Nominal Workflow

## Scope
Nominal detector-level alphaS chain: histmaker -> rabbit fit -> impacts/FoM.

## Canonical Facts
- Histmaker wrapper: `workflows/histmaker.sh`
- Core histmaker: `${WREM_BASE}/scripts/histmakers/mz_dilepton.py`
- Fitter wrapper: `workflows/fitter.sh`
- Fit setup: `${WREM_BASE}/scripts/rabbit/setupRabbit.py`
- Fit execution: `rabbit_fit.py`
- Impacts plot wrapper: `workflows/pullsAndImpacts.sh`

## Rules I Should Follow
- Launch through `run workflows/<step>.sh` for timestamped logs in `logs/`.
- Prefer `-e "--flag=value"` format for wrapper extra args.
- Use the writer line `Output saved in <path>` as authoritative output location.

## Standard Commands
```bash
run workflows/histmaker.sh
run workflows/fitter.sh <histmaker_hdf5>
workflows/pullsAndImpacts.sh <fitresults_hdf5> -p <tag>
```

Text check equivalent:
```bash
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults_hdf5> --scale 2.0
python /home/submit/lavezzo/alphaS/gh/WRemnants/rabbit/bin/rabbit_print_impacts.py <fitresults_hdf5> --globalImpacts --scale 2.0
```

## Common Pitfalls
- `-e "--maxFiles 10"` can parse incorrectly; use `-e "--maxFiles=10"`.
- Non-TTY sessions can break naive `tee /dev/tty` usage.

## Last Updated
- 2026-02-16

## Source
- Migration from legacy nominal workflow notes (2026-02-16)
