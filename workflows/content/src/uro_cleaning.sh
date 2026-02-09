#!/usr/bin/env bash
set -euo pipefail

uro_cleaning() {
    local urls_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${urls_file}" ]]; then
        echo "Usage: uro_cleaning <urls_file> [output_path]" >&2
        return 1
    fi

    if [[ ! -f "${urls_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${urls_file}" ]]; then
            urls_file="${repo_root}/${urls_file}"
        else
            echo "URLs file not found: ${urls_file}" >&2
            return 1
        fi
    fi

    local urls_dir="${output_path}/subs/urls"
    local cleaned_urls_file="${urls_dir}/cleaned.all.urls.txt"

    mkdir -p "${urls_dir}"

    if [[ -s "${cleaned_urls_file}" ]]; then
        local tmp_cleaned
        tmp_cleaned="$(mktemp)"
        trap '[[ -n "${tmp_cleaned:-}" ]] && rm -f "${tmp_cleaned}"' EXIT
        cat "${urls_file}" | uro > "${tmp_cleaned}"
        if [[ -s "${tmp_cleaned}" ]]; then
            cat "${tmp_cleaned}" | anew "${cleaned_urls_file}"
        fi
    else
        cat "${urls_file}" | uro > "${cleaned_urls_file}"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    uro_clean_urls "$@"
fi
