#!/usr/bin/env bash
set -euo pipefail

nuclei_js_scan() {
    local js_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${3:-false}"

    if [[ -z "${js_file}" ]]; then
        echo "Usage: nuclei_js_scan <js_file> [output_path] [notify]" >&2
        return 1
    fi

    if [[ ! -f "${js_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${js_file}" ]]; then
            js_file="${repo_root}/${js_file}"
        else
            echo "JS file list not found: ${js_file}" >&2
            return 1
        fi
    fi

    local js_dir="${output_path}/content/javascript"
    local output_file="${js_dir}/nuclei.javascript.scan.txt"
    local tmp_output=""

    mkdir -p "${js_dir}"

    tmp_output="$(mktemp)"
    trap '[[ -n "${tmp_output:-}" ]] && rm -f "${tmp_output}"' EXIT

    nuclei -silent -l "${js_file}" -tags js,secrets,exposure,token -o "${tmp_output}" || true

    if [[ -s "${tmp_output}" ]]; then
        cat "${tmp_output}" | anew "${output_file}" || true

        if [[ "${notify_enabled}" == "true" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
            {
                echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] Nuclei JS Findings\n"
                cat "${tmp_output}"
            } | notify -bulk -provider telegram || true
        fi
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    nuclei_js_scan "$@"
fi
