#!/usr/bin/env bash
set -euo pipefail

gobuster_fuzzing() {
    local subs_file="${1:-}"
    local output_path="${2:-output}"
    local wordlist="${3:-/usr/share/wordlists/dirb/common.txt}"
    local notify_enabled="${4:-false}"

    if [[ -z "${subs_file}" || ! -f "${subs_file}" ]]; then
        echo "Usage: gobuster_fuzzing <subs_file> [output_path] [wordlist] [notify_enabled]" >&2
        return 1
    fi

    local fuzz_dir="${output_path}/content/urls/fuzzing"
    local all_urls_file="${output_path}/content/urls/all.urls.txt"
    mkdir -p "${fuzz_dir}" "$(dirname "${all_urls_file}")"
    touch "${all_urls_file}"

    process_sub() {
        local sub="$1"
        sub=$(echo "${sub}" | tr -d '\r' | xargs)
        [[ -z "${sub}" || "${sub}" =~ ^# ]] && return 0

        local base_url="${sub}"
        [[ ! "${sub}" =~ ^http ]] && base_url="https://${sub}"
        
        local safe_name=$(echo "${base_url}" | sed 's/[^a-zA-Z0-9]/_/g')
        local out_raw="${fuzz_dir}/gobuster.${safe_name}.txt"
        local tmp_new=$(mktemp)

        echo "[+] Fuzzing ${base_url}..." >&2


        gobuster dir -u "${base_url}/" -w "${wordlist}" -q --no-error -b "404,400" -o "${out_raw}" \
        -t 5 \
        --delay 200ms \
        -a "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
        --timeout 5s \
        || true


        if [[ -s "${out_raw}" ]]; then
            grep "Found:" "${out_raw}" | awk '{print $2}' | while read -r path; do
                echo "${base_url}${path}"
            done | anew "${all_urls_file}" > "${tmp_new}"

            if [[ -s "${tmp_new}" ]]; then
                echo "[!] New matches for ${sub} saved." >&2
                if [[ "${notify_enabled}" == "true" ]]; then
                    notify -bulk -data "${tmp_new}" -msg "Gobuster discovery on ${sub}" || true
                fi
            fi
        fi
        rm -f "${tmp_new}"
    }

    export -f process_sub
    export wordlist fuzz_dir all_urls_file notify_enabled

    grep -vE '^\s*#|^\s*$' "${subs_file}" | \
        xargs -I{} -P 5 bash -c 'process_sub "$1"' _ "{}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    gobuster_fuzzing "$@"
fi