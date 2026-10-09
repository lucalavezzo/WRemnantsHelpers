#!/bin/bash
# Assemble merged_full_bin0xzero/cache.npz = merged_full/cache.npz with fo.npy replaced by the
# patched one from zero_bin0_crossterms.py. `zip --copy` carries every other member over RAW
# (no recompression of the 143.5 GB rules blob); the original cache is only read.
set -euo pipefail
SRC=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921/merged_full
DST=/ceph/submit/data/group/cms/store/user/lavezzo/alphaS/scetlib_ad_caches/pdf62_y35_260921/merged_full_bin0xzero
echo "=== start $(date -Is)"
rm -f $DST/cache.npz
zip -q $SRC/cache.npz --copy format.npy n_eig.npy has_as.npy has_muf.npy rules.npy bins.npy anchor.npy names.npy --out $DST/cache.npz
( cd $DST/tmp && zip -q $DST/cache.npz fo.npy )
cp $SRC/cache.conf $DST/cache.conf
cp $SRC/build.log $DST/build_of_source_cache.log
cat > $DST/README.txt <<'TXT'
QUICK-PATCHED copy of ../merged_full (Luca's option b, 2026-09-24).
Identical to merged_full except fo.npy: the fixed-order eigenvector cross terms of the 15 bins
with qT in [0, 0.5] (the bin containing the 0.1 GeV nonsingular cutoff) are ZEROED, because
scetlib-cms 2dd978a built them from unsubtracted V+jet below the cut. Genuine values there are
~3-5e-4 of sigma at seed-sized eigenvector displacements.
See WRemnantsHelpers/studies/alphas-scan-discontinuity/260924-bilin-nons-cut/LOGBOOK.md
TXT
echo "=== members:"; python3 -c "import zipfile; [print(' ',i.filename,i.file_size) for i in zipfile.ZipFile('$DST/cache.npz').infolist()]"
echo "=== exit 0 $(date -Is)"
