#!/usr/bin/env bash
set -euo pipefail

download_js_files() {
    local urls_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${urls_file}" ]]; then
        echo "Usage: download_js_files <urls_file> [output_path]" >&2
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

    local js_dir="${output_path}/content/javascript"
    local downloads_dir="${js_dir}/js_files"
    local beautified_dir="${js_dir}/beautified"

    mkdir -p "${downloads_dir}" "${beautified_dir}"

    while IFS= read -r url; do
        url="${url//$'\r'/}"
        [[ -z "${url}" ]] && continue
        [[ "${url}" =~ ^[[:space:]]*# ]] && continue
        wget -q "${url}" -P "${downloads_dir}" || true
    done < "${urls_file}"

    if command -v js-beautify >/dev/null 2>&1; then
        for file in "${downloads_dir}"/*.js; do
            [[ -e "${file}" ]] || continue
            js-beautify < "${file}" > "${beautified_dir}/$(basename "${file}")" || true
        done
    else
        echo "js-beautify not found in PATH. Skipping beautify step." >&2
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    download_js_files "$@"
fi
