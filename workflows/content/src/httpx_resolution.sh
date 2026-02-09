#!/usr/bin/env bash
set -euo pipefail

httpx_resolution() {
    local urls_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${urls_file}" ]]; then
        echo "Usage: httpx_resolution <urls_file> [output_path]" >&2
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

    local urls_dir="${output_path}/content/urls"
    local live_urls_file="${urls_dir}/all.live.urls.txt"

    mkdir -p "${urls_dir}"

    cat "${urls_file}" | \
        httpx -silent -mc 200 -threads 100 -o "${live_urls_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    httpx_resolution "$@"
fi
