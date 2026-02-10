#!/usr/bin/env bash
set -euo pipefail

arjun_enum() {
    local input_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${input_file}" ]]; then
        echo "Usage: arjun_enum <input_file> [output_path]" >&2
        return 1
    fi

    if [[ ! -f "${input_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${input_file}" ]]; then
            input_file="${repo_root}/${input_file}"
        else
            echo "Input file not found: ${input_file}" >&2
            return 1
        fi
    fi

    local urls_dir="${output_path}/content/urls"
    local arjun_dir="${urls_dir}/arjun"
    local arjun_output_file="${urls_dir}/all.arjun.urls.txt"

    mkdir -p "${arjun_dir}"

    arjun -i "${input_file}" -oT "${arjun_output_file}"

    cat "${arjun_output_file}" | anew "${urls_dir}/all.urls.txt" || true
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    arjun_enum "$@"
fi
