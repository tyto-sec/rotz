#!/usr/bin/env bash
set -euo pipefail

subjs_enum() {
    local urls_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${urls_file}" ]]; then
        echo "Usage: subjs_enum <urls_file> [output_path]" >&2
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
    local all_js_file="${js_dir}/all.javascript.txt"
    local subs_file="${output_path}/subs/all.subs.txt"
    local filtered_input_file=""
    local tmp_js_file=""
    local filtered_js_file=""
    local filtered_existing_file=""
    local final_js_file=""

    mkdir -p "${js_dir}"

    filtered_input_file="$(mktemp)"
    tmp_js_file="$(mktemp)"
    filtered_js_file="$(mktemp)"
    filtered_existing_file="$(mktemp)"
    final_js_file="$(mktemp)"
    trap '[[ -n "${filtered_input_file:-}" ]] && rm -f "${filtered_input_file}"; [[ -n "${tmp_js_file:-}" ]] && rm -f "${tmp_js_file}"; [[ -n "${filtered_js_file:-}" ]] && rm -f "${filtered_js_file}"; [[ -n "${filtered_existing_file:-}" ]] && rm -f "${filtered_existing_file}"; [[ -n "${final_js_file:-}" ]] && rm -f "${final_js_file}"' EXIT

    if [[ -s "${subs_file}" ]]; then
        python3 - "${subs_file}" "${urls_file}" "${filtered_input_file}" <<'PY'
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
        cp "${urls_file}" "${filtered_input_file}"
    fi

    cat "${filtered_input_file}" | subjs | sort -u > "${tmp_js_file}"

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

        if [[ -s "${all_js_file}" ]] && [[ -s "${subs_file}" ]]; then
            python3 - "${subs_file}" "${all_js_file}" "${filtered_existing_file}" <<'PY'
import sys
from urllib.parse import urlparse

subs_path, in_path, out_path = sys.argv[1:4]
with open(subs_path, 'r', encoding='utf-8', errors='ignore') as f:
    subs = {line.strip().rstrip('.').lower() for line in f if line.strip() and not line.lstrip().startswith('#')}

def host_from_url(url: str) -> str:
    url = url.strip()
    if not url:
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
        elif [[ -s "${all_js_file}" ]]; then
            cp "${all_js_file}" "${filtered_existing_file}"
        fi

        cat "${filtered_existing_file}" "${filtered_js_file}" 2>/dev/null | sort -u > "${final_js_file}" || true
        if [[ -s "${final_js_file}" ]]; then
            cp "${final_js_file}" "${all_js_file}"
        fi
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    subjs_enum "$@"
fi
