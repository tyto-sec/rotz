#!/usr/bin/env bash
set -euo pipefail

gobuster_vhost_fuzzing() {
    local subs_file="${1:-}"
    local output_path="${2:-output}"
    local wordlist="${3:-wordlists/subdomains/subdomains-top1million-5000.txt}"
    local notify_enabled="${4:-false}"

    if [[ -z "${subs_file}" || ! -f "${subs_file}" ]]; then
        echo "Usage: gobuster_vhost_fuzzing <subs_file> [output_path] [wordlist] [notify]" >&2
        return 1
    fi

    local fuzz_dir="${output_path}/content/urls/fuzzing"
    local all_subs_file="${output_path}/subs/all.subs.txt"
    mkdir -p "${fuzz_dir}" "$(dirname "${all_subs_file}")"
    touch "${all_subs_file}"

    process_sub() {
        local line="$1"
        line=$(echo "${line}" | tr -d '\r' | xargs)
        [[ -z "${line}" || "${line}" =~ ^# ]] && return 0

        local base_url
        if [[ "${line}" =~ ^http ]]; then
            base_url="${line%/}"
        else
            base_url="https://${line%/}"
        fi

        local safe_name=$(echo "${base_url}" | sed -E 's|^https?://||' | sed 's/[^a-zA-Z0-9]/_/g')
        local out_raw="${fuzz_dir}/gobuster.vhost.${safe_name}.txt"
        local tmp_new=$(mktemp)

        echo "[+] VHOST fuzzing ${base_url}..." >&2

        gobuster vhost -u "${base_url}" -w "${wordlist}" --append-domain -q   \
        -t 5 \
        --delay 200ms \
        -a "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
        --timeout 5s \
        --no-error -o "${out_raw}" || true
        
        if [[ -s "${out_raw}" ]]; then
            grep "Found:" "${out_raw}" | awk '{print $2}' | anew "${all_subs_file}" > "${tmp_new}"

            if [[ -s "${tmp_new}" ]]; then
                echo "[!] New VHOSTs found for ${target}!" >&2
                if [[ "${notify_enabled}" == "true" ]]; then
                    notify -bulk -data "${tmp_new}" -msg "Gobuster VHOST discovery on ${target}" || true
                fi
            fi
        fi
        rm -f "${tmp_new}"
    }

    export -f process_sub
    export wordlist fuzz_dir all_subs_file notify_enabled

    grep -vE '^\s*#|^\s*$' "${subs_file}" | \
        xargs -I{} -P 5 bash -c 'process_sub "$1"' _ "{}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    gobuster_vhost_fuzzing "$@"
fi