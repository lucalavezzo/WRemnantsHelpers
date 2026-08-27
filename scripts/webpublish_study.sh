#!/bin/bash
# Publish a study's logbooks to the webdir, by symlink.
#
# Idempotent: safe to run every time a study is started or resumed (the /study skill does
# exactly that). There is no build step -- the viewer reads the markdown live, so this only
# ever has to create the symlink once per study and keep the viewer files current.
#
#   scripts/webpublish_study.sh <slug> [<slug> ...]
#   scripts/webpublish_study.sh --all
#   scripts/webpublish_study.sh --unpublish <slug>
#   scripts/webpublish_study.sh --force <slug>      # override the exposure check
#
# ~/public_html has NO authentication. The symlink publishes everything in the study
# directory, now and later, so the exposure check below refuses studies holding session
# transcripts, *.jsonl, or files over 5 MB until you pass --force.

set -uo pipefail

HERE=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)
REPO=$(dirname "$HERE")
STUDIES="$REPO/studies"
WEBROOT="$HOME/public_html/alphaS/studies"
MAXMB=5

FORCE=0
UNPUB=0
ALL=0
SLUGS=()
for a in "$@"; do
    case "$a" in
        --force)     FORCE=1 ;;
        --unpublish) UNPUB=1 ;;
        --all)       ALL=1 ;;
        -h|--help)   sed -n '2,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
        -*)          echo "unknown flag: $a" >&2; exit 1 ;;
        *)           SLUGS+=("$a") ;;
    esac
done

if [[ $ALL -eq 1 ]]; then
    while IFS= read -r p; do SLUGS+=("$(basename "$(dirname "$p")")"); done \
        < <(find "$STUDIES" -mindepth 2 -maxdepth 2 -name LOGBOOK.md | sort)
fi
if [[ ${#SLUGS[@]} -eq 0 ]]; then
    echo "usage: $(basename "$0") <slug> [<slug> ...] | --all | --unpublish <slug>" >&2
    exit 1
fi

# ---- viewer: install/refresh once, shared by every study ----
install_viewer() {
    mkdir -p "$WEBROOT" || return 1
    local src="$REPO/scripts/templates/study_viewer.php"
    local vend="$REPO/scripts/templates/vendor/marked.min.js"
    [[ -f $src  ]] || { echo "MISSING: $src" >&2; return 1; }
    [[ -f $vend ]] || { echo "MISSING: $vend" >&2; return 1; }
    for pair in "$src:$WEBROOT/index.php" "$vend:$WEBROOT/marked.min.js"; do
        local from=${pair%%:*} to=${pair##*:}
        if ! cmp -s "$from" "$to"; then
            cp "$from" "$to" && echo "  installed $(basename "$to")"
        fi
    done
    return 0
}

# ---- exposure check ----
exposure_report() {
    local dir=$1 found=0
    if [[ -d "$dir/sessions" ]]; then
        echo "    sessions/  ($(du -sh "$dir/sessions" 2>/dev/null | cut -f1) of session transcripts)"
        found=1
    fi
    local f
    while IFS= read -r f; do
        [[ -z $f ]] && continue
        echo "    ${f#"$dir/"}  (jsonl)"
        found=1
    done < <(find "$dir" -type f -name '*.jsonl' -not -path "$dir/sessions/*" 2>/dev/null | head -10)
    while IFS= read -r f; do
        [[ -z $f ]] && continue
        echo "    ${f#"$dir/"}  ($(( $(stat -c%s "$f") / 1048576 )) MB)"
        found=1
    done < <(find "$dir" -type f -size +${MAXMB}M -not -name '*.jsonl' 2>/dev/null | head -10)
    return $found
}

rc=0
install_viewer || exit 1

for slug in "${SLUGS[@]}"; do
    slug=${slug%/}
    slug=$(basename "$slug")
    src="$STUDIES/$slug"
    link="$WEBROOT/$slug"

    if [[ $UNPUB -eq 1 ]]; then
        if [[ -L $link ]]; then rm "$link"; echo "unpublished: $slug"
        else echo "not published: $slug"; fi
        continue
    fi

    if [[ ! -d $src ]]; then
        echo "SKIP $slug — no such study ($src)" >&2; rc=1; continue
    fi
    if [[ ! -f $src/LOGBOOK.md ]]; then
        echo "SKIP $slug — no LOGBOOK.md; copy studies/_TEMPLATE/LOGBOOK.md into it first" >&2
        rc=1; continue
    fi

    if [[ $FORCE -eq 0 ]]; then
        report=$(exposure_report "$src")
        if [[ -n $report ]]; then
            echo "REFUSING $slug — public_html has no auth and this study holds:" >&2
            echo "$report" >&2
            echo "  Move it out (bulk outputs belong on ceph), or re-run with --force." >&2
            rc=2; continue
        fi
    fi

    if [[ -L $link ]]; then
        cur=$(readlink -f "$link")
        if [[ $cur != "$(readlink -f "$src")" ]]; then
            ln -sfn "$src" "$link"; echo "relinked: $slug"
        fi
    elif [[ -e $link ]]; then
        echo "SKIP $slug — $link exists and is not a symlink" >&2; rc=1; continue
    else
        ln -s "$src" "$link"; echo "published: $slug"
    fi

    ntask=$(find "$src" -mindepth 2 -maxdepth 2 -name LOGBOOK.md 2>/dev/null | wc -l)
    echo "  https://submit.mit.edu/~$USER/alphaS/studies/#$slug   ($ntask task$([[ $ntask -eq 1 ]] || echo s))"
done

exit $rc
