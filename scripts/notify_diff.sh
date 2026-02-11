#!/usr/bin/env bash
set -euo pipefail

# Usage: scripts/notify_diff.sh [dir]
# Default dir: ./output
DIR="${1:-./output}"

# Verifica se a ferramenta 'notify' está instalada
HAS_NOTIFY=0
command -v notify >/dev/null 2>&1 || HAS_NOTIFY=1

shopt -s nullglob

# collect unique suffix keys (part after first underscore)
keys=()
for f in "$DIR"/*.txt; do
    [ -f "$f" ] || continue
    bn=$(basename "$f")
    keys+=("${bn#*_}")
done

if [ "${#keys[@]}" -eq 0 ]; then
    echo "No files found in $DIR"
    exit 0
fi

# uniq
IFS=$'\n' read -r -d '' -a uniq_keys < <(printf "%s\n" "${keys[@]}" | sort -u && printf '\0')

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

for key in "${uniq_keys[@]}"; do
    files=("$DIR"/[0-9]*_"$key")
    
    if [ ${#files[@]} -lt 2 ]; then
        continue
    fi
    
    # Ordenar via mapfile
    mapfile -t files < <(printf "%s\n" "${files[@]}" | sort -r)

    latest="${files[0]}"
    for other in "${files[@]:1}"; do
        sorted_latest="$tmpdir/lt.$$"
        sorted_other="$tmpdir/ot.$$"
        sort -u "$latest" >"$sorted_latest"
        sort -u "$other" >"$sorted_other"

        diff_lines=$(comm -23 "$sorted_latest" "$sorted_other" || true)
        diff_count=0
        if [ -n "$diff_lines" ]; then
            diff_count=$(printf "%s\n" "$diff_lines" | sed '/^\s*$/d' | wc -l | tr -d ' ')
        fi

        if [ "$diff_count" -gt 0 ]; then
            preview=$(printf "%s\n" "$diff_lines" | sed -n '1,10p')
            
            # Monta a mensagem formatada para o notify
            message=$(printf "New Domains: %s (%s novos)\n%s ≠ %s\n\nNovos:\n%s" \
                "$key" "$diff_count" "$(basename "$latest")" "$(basename "$other")" "$preview")
            
            if [ "$HAS_NOTIFY" -eq 0 ]; then
                # Envia para a ferramenta notify (Discord, Telegram, Slack, etc)
                echo "$message" | notify
            else
                # Fallback para o terminal se o notify não estiver no PATH
                printf "============================\n%s\n============================\n\n" "$message"
            fi
        fi
        rm -f "$sorted_latest" "$sorted_other"
    done
done