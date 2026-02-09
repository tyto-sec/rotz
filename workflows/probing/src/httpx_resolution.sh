#!/usr/bin/env bash
set -euo pipefail

httpx_resolution() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${3:-false}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: httpx_resolution <subs_file> [output_path] [notify]" >&2
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

    local live_dir="${output_path}/subs"
    local all_live_file="${live_dir}/all.live.subs.txt"
    local httpx_output_file=""
    local new_live_file=""
    local first_run=false

    mkdir -p "${live_dir}"

    if [[ ! -s "${all_live_file}" ]]; then
        first_run=true
    fi

    httpx_output_file="$(mktemp)"
    new_live_file="$(mktemp)"
    trap '[[ -n "${httpx_output_file:-}" ]] && rm -f "${httpx_output_file}"; [[ -n "${new_live_file:-}" ]] && rm -f "${new_live_file}"' EXIT

    cat "${subs_file}" | \
        httpx -silent -threads 200 -p 80,443,8080,8443,3000,8000,9000,5000,8888,8181 -o "${httpx_output_file}"

    sort -u "${httpx_output_file}" > "${new_live_file}"

    if [[ -f "${all_live_file}" ]]; then
        comm -13 <(sort "${all_live_file}") <(sort "${new_live_file}") > "${httpx_output_file}"
        mv "${httpx_output_file}" "${new_live_file}"
    fi

    if [[ -s "${new_live_file}" ]]; then
        if [[ "${notify_enabled}" == "true" ]] && [[ "${first_run}" == "false" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
            {
                echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Live Subdomains (httpx)\n"
                cat "${new_live_file}"
            } | notify -bulk -provider telegram || true
        fi
        cat "${new_live_file}" | anew "${all_live_file}"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    httpx_resolution "$@"
fi
