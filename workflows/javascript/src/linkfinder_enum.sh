#!/usr/bin/env bash
set -euo pipefail

linkfinder_enum() {
    local input_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${input_file}" ]]; then
        echo "Usage: linkfinder_enum <input_file> [output_path]" >&2
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

    local js_dir="${output_path}/content/javascript"
    local urls_dir="${output_path}/content/url"
    local wordlists_dir="${output_path}/content/wordlists"
    local linkfinder_file="${js_dir}/linkfinder.content.txt"
    local linkfinder_urls_file="${urls_dir}/linkfinder.url.txt"
    local all_urls_file="${urls_dir}/all.url.txt"
    local all_paths_file="${wordlists_dir}/all.paths.txt"
    local subs_file="${output_path}/subs/all.subs.txt"
    local filtered_input_file=""
    local tmp_results=""
    local filtered_results=""
    local filtered_existing=""
    local final_results=""
    local linkfinder_cmd=()

    mkdir -p "${js_dir}" "${urls_dir}" "${wordlists_dir}"

        if command -v linkfinder >/dev/null 2>&1; then
            linkfinder_cmd=(linkfinder)
        elif command -v linkfinder.py >/dev/null 2>&1; then
            linkfinder_cmd=(linkfinder.py)
        elif command -v python3 >/dev/null 2>&1; then
            linkfinder_cmd=(python3 -m linkfinder)
        elif command -v pipx >/dev/null 2>&1; then
            linkfinder_cmd=(pipx run linkfinder)
        else
            echo "LinkFinder not found in PATH" >&2
            return 1
        fi

    filtered_input_file="$(mktemp)"
    tmp_results="$(mktemp)"
    filtered_results="$(mktemp)"
    filtered_existing="$(mktemp)"
    final_results="$(mktemp)"
    trap '[[ -n "${filtered_input_file:-}" ]] && rm -f "${filtered_input_file}"; [[ -n "${tmp_results:-}" ]] && rm -f "${tmp_results}"; [[ -n "${filtered_results:-}" ]] && rm -f "${filtered_results}"; [[ -n "${filtered_existing:-}" ]] && rm -f "${filtered_existing}"; [[ -n "${final_results:-}" ]] && rm -f "${final_results}"' EXIT

    if [[ -s "${subs_file}" ]]; then
        python3 - "${subs_file}" "${input_file}" "${filtered_input_file}" <<'PY'
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
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").rstrip('.').lower()
        return host
    except Exception:
        return ""

with open(in_path, 'r', encoding='utf-8', errors='ignore') as fin, open(out_path, 'w', encoding='utf-8') as fout:
    for line in fin:
        host = host_from_url(line)
        if host and host in subs:
            fout.write(line.rstrip() + "\n")
PY
    else
        cp "${input_file}" "${filtered_input_file}"
    fi

    while IFS= read -r line; do
        line="${line//$'\r'/}"
        [[ -z "${line}" ]] && continue
        [[ "${line}" =~ ^[[:space:]]*# ]] && continue
        if [[ "${line}" != *".js"* ]]; then
            continue
        fi
        "${linkfinder_cmd[@]}" -i "${line}" -o cli >> "${tmp_results}" || true
    done < "${filtered_input_file}"

    if [[ -s "${tmp_results}" ]]; then
        if [[ -s "${subs_file}" ]]; then
            python3 - "${subs_file}" "${tmp_results}" "${filtered_results}" <<'PY'
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
            cp "${tmp_results}" "${filtered_results}"
        fi

        if [[ -s "${linkfinder_file}" ]] && [[ -s "${subs_file}" ]]; then
            python3 - "${subs_file}" "${linkfinder_file}" "${filtered_existing}" <<'PY'
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
        elif [[ -s "${linkfinder_file}" ]]; then
            cp "${linkfinder_file}" "${filtered_existing}"
        fi

        cat "${filtered_existing}" "${filtered_results}" 2>/dev/null | sort -u > "${final_results}" || true
        if [[ -s "${final_results}" ]]; then
            cp "${final_results}" "${linkfinder_file}"

            python3 - "${final_results}" "${subs_file}" "${linkfinder_urls_file}" "${all_urls_file}" "${all_paths_file}" <<'PY'
import re
import sys
from urllib.parse import urlparse

raw_path, subs_path, out_linkfinder, out_all, out_paths = sys.argv[1:6]

subs = set()
try:
    with open(subs_path, 'r', encoding='utf-8', errors='ignore') as f:
        subs = {line.strip().rstrip('.').lower() for line in f if line.strip() and not line.lstrip().startswith('#')}
except FileNotFoundError:
    subs = set()

url_re = re.compile(r"https?://[^\s\)\]\"']+")

def host_in_subs(url: str) -> bool:
    if not subs:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = (parsed.hostname or "").rstrip('.').lower()
        return host in subs
    except Exception:
        return False

urls = []
paths = []
with open(raw_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        for match in url_re.findall(line):
            if host_in_subs(match):
                urls.append(match)
                try:
                    p = urlparse(match).path
                    if p:
                        paths.append(p)
                except Exception:
                    pass

def write_unique(path: str, items):
    if not items:
        return
    unique = sorted(set(items))
    with open(path, 'a', encoding='utf-8') as f:
        for item in unique:
            f.write(item + "\n")

write_unique(out_linkfinder, urls)
write_unique(out_all, urls)
write_unique(out_paths, paths)
PY
        fi
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    linkfinder_enum "$@"
fi
