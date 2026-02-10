#!/usr/bin/env bash
set -euo pipefail

paramspider_enum() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: paramspider_enum <subs_file> [output_path]" >&2
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

    local urls_dir="${output_path}/content/urls"
    local paramspider_dir="${urls_dir}/paramspider"
    local all_paramspider_file="${urls_dir}/all.paramspider.urls.txt"

    mkdir -p "${paramspider_dir}"

    paramspider -l "${subs_file}"

    if [[ -d "results" ]]; then
        cp -r results/* "${paramspider_dir}/" || true
        rm -rf results
    fi

    if [[ -d "${paramspider_dir}" ]]; then
        cat "${paramspider_dir}"/* 2>/dev/null | anew "${all_paramspider_file}" || true
    fi

    cat "${all_paramspider_file}" | anew "${urls_dir}/all.urls.txt" || true

}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    paramspider_enum "$@"
fi
