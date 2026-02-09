#!/usr/bin/env bash
set -euo pipefail

gowitness_enum() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: gowitness_enum <subs_file> [output_path]" >&2
        return 1
    fi

    if [[ ! -f "${subs_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${subs_file}" ]]; then
            subs_file="${repo_root}/${subs_file}"
        else
            echo "Subdomains file not found: ${subs_file}" >&2
            return 1
        fi
    fi

    local screenshots_dir="${output_path}/content/screenshots"
    local enum_dir="${output_path}/content/enum"
    local jsonl_file="${enum_dir}/gowitness.enum.subs.jsonl"
    local json_file="${enum_dir}/gowitness.enum.subs.json"
    local csv_file="${enum_dir}/gowitness.enum.subs.csv"

    mkdir -p "${screenshots_dir}" "${enum_dir}"

    gowitness scan file -f "${subs_file}" \
        --write-csv --write-csv-file "${csv_file}" \
        --write-jsonl --write-jsonl-file "${jsonl_file}" \
        --screenshot-skip-save

    if [[ -s "${jsonl_file}" ]]; then
        jq -s '.' "${jsonl_file}" > "${json_file}"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    gowitness_enum "$@"
fi
