#!/usr/bin/env bash
set -euo pipefail

katana_js_enum() {
    local javascript_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${javascript_file}" ]]; then
        echo "Usage: katana_js_enum <javascript_file> [output_path]" >&2
        return 1
    fi

    if [[ ! -f "${javascript_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${javascript_file}" ]]; then
            javascript_file="${repo_root}/${javascript_file}"
        else
            echo "JavaScript file list not found: ${javascript_file}" >&2
            return 1
        fi
    fi

    local urls_dir="${output_path}/content/urls"
    local all_urls_file="${urls_dir}/all.urls.txt"
    local subs_file="${output_path}/subs/all.subs.txt"
    local tmp_js_file=""
    local filtered_js_file=""

    mkdir -p "${urls_dir}"

    tmp_js_file="$(mktemp)"
    filtered_js_file="$(mktemp)"
    cat "${javascript_file}" | \
        katana -jc -c 2 -p 2 -rd 1 -rl 30 > "${tmp_js_file}"

    if [[ -s "${tmp_js_file}" ]]; then
        if [[ -s "${subs_file}" ]]; then
            python3 - "${subs_file}" "${tmp_js_file}" "${filtered_js_file}" <<'PY'
import sys
from urllib.parse import urlparse

subs_path, in_path, out_path = sys.argv[1:4]
with open(subs_path, 'r', encoding='utf-8', errors='ignore') as f:
    subs = {line.strip().rstrip('.').lower() for line in f if line.strip() and not line.lstrip().startswith('#')}

def host_from_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if url.startswith("data:"):
        return ""
    if url.startswith("//"):
        url = "http:" + url
    if "://" not in url:
        url = "http://" + url
    parsed = urlparse(url)
    host = (parsed.hostname or "").rstrip('.').lower()
    return host

with open(in_path, 'r', encoding='utf-8', errors='ignore') as fin, open(out_path, 'w', encoding='utf-8') as fout:
    for line in fin:
        host = host_from_url(line)
        if host and host in subs:
            fout.write(line.rstrip() + "\n")
PY
        else
            cp "${tmp_js_file}" "${filtered_js_file}"
        fi

        if [[ -s "${filtered_js_file}" ]]; then
            cat "${filtered_js_file}" | anew "${all_urls_file}" || true
        fi
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    katana_js_enum "$@"
fi
