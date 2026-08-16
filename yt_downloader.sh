#!/usr/bin/env bash
#
# Shell port of yt_downloader.py: downloads every video listed in conf.json5
# with yt-dlp, one per "titles" entry.
#
# Usage: ./yt_downloader.sh [-n|--dry-run] [conf-file]

set -u

DEFAULT_MAX_HEIGHT=1080

dry_run=0
conf_file="conf.json5"

while [ $# -gt 0 ]; do
    case "$1" in
        -n|--dry-run) dry_run=1 ;;
        -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
        -*) echo "unknown option: $1" >&2; exit 2 ;;
        *) conf_file="$1" ;;
    esac
    shift
done

for cmd in yt-dlp jq; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "$cmd is not installed" >&2; exit 1; }
done

[ -f "$conf_file" ] || { echo "no such file: $conf_file" >&2; exit 1; }

# conf.json5 is JSON5: drop whole-line // comments so jq can read it. If that is
# not enough (trailing commas, unquoted keys), fall back to python3's json5.
read_conf() {
    local stripped
    stripped=$(sed -e 's|^[[:space:]]*//.*$||' "$conf_file")

    if printf '%s' "$stripped" | jq -e . >/dev/null 2>&1; then
        printf '%s' "$stripped"
    else
        python3 -c 'import json, json5, sys; json.dump(json5.load(open(sys.argv[1])), sys.stdout)' "$conf_file"
    fi
}

conf=$(read_conf) || exit 1

get() { printf '%s' "$conf" | jq -r "$1"; }

url_template=$(get '.url_template')
referer=$(get '.referer')
name=$(get '.name')
max_height=$(get ".max_height // $DEFAULT_MAX_HEIGHT")

mkdir -p "$name"

is_downloaded() {
    local dir="$1" title="$2" f
    for f in "$dir/$title".*; do
        [ -e "$f" ] || continue
        case "$f" in
            *.part|*.ytdl) continue ;;
        esac
        return 0
    done

    return 1
}

download() {
    local url="$1" title="$2"

    if is_downloaded "$name" "$title"; then
        echo "skipping (already downloaded): $title"
        return 0
    fi

    set -- yt-dlp \
        -S "res:$max_height" \
        --referer "$referer" \
        --force-generic-extractor \
        "$url" \
        -o "$name/$title.%(ext)s"

    echo "$*"
    [ "$dry_run" -eq 1 ] && return 0

    "$@" || { echo "failed (exit $?): $title" >&2; return 1; }
}

failed=0
while IFS=$'\t' read -r video_id title; do
    [ -n "$video_id" ] || continue
    echo "$video_id: $title"

    url="${url_template//\{index\}/$video_id}"
    download "$url" "$title" || failed=$((failed + 1))
done <<EOF
$(get '.titles | to_entries[] | "\(.key)\t\(.value)"')
EOF

if [ "$failed" -gt 0 ]; then
    echo "$failed download(s) failed" >&2
    exit 1
fi
