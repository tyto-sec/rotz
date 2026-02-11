#!/usr/bin/env bash
set -euo pipefail

katana_enum() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: katana_enum <subs_file> [output_path]" >&2
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
    local tmp_dir="${output_path}/content/tmp"
    local all_urls_file="${urls_dir}/all.urls.txt"
    local tmp_urls_file=""
    local normalized_subs_file=""

    mkdir -p "${urls_dir}" "${tmp_dir}"

    tmp_urls_file="$(mktemp)"
    normalized_subs_file="$(mktemp)"
    trap '[[ -n "${tmp_urls_file:-}" ]] && rm -f "${tmp_urls_file}"; [[ -n "${normalized_subs_file:-}" ]] && rm -f "${normalized_subs_file}"' EXIT

    python3 - "${subs_file}" "${normalized_subs_file}" <<'PY'
import sys
from urllib.parse import urlparse

in_path, out_path = sys.argv[1:3]

def normalize(line: str) -> str:
    line = line.strip()
    if not line or line.startswith('#'):
        return ""
    if line.startswith("//"):
        line = "http:" + line
    if "://" not in line:
        return line.rstrip('.').lower()
    parsed = urlparse(line)
    host = (parsed.hostname or "").rstrip('.').lower()
    return host

seen = set()
with open(in_path, 'r', encoding='utf-8', errors='ignore') as fin, open(out_path, 'w', encoding='utf-8') as fout:
    for raw in fin:
        host = normalize(raw)
        if host and host not in seen:
            seen.add(host)
            fout.write(host + "\n")
PY

    cat "${normalized_subs_file}" | \
        katana -c 2 -p 2 -rd 1 -rl 30 > "${tmp_urls_file}"

    if [[ -s "${tmp_urls_file}" ]]; then
        cat "${tmp_urls_file}" | anew "${all_urls_file}"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    katana_enum "$@"
fi
