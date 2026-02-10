#!/usr/bin/env bash
set -euo pipefail

cewl_wordlist_generation() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: cewl_wordlist_generation <subs_file> [output_path]" >&2
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

    local fuzz_dir="${output_path}/content/wordlists"
    local words_file="${fuzz_dir}/cewl.word.list"
    local tmp_words_file=""

    mkdir -p "${fuzz_dir}"

    tmp_words_file="$(mktemp)"
    trap '[[ -n "${tmp_words_file:-}" ]] && rm -f "${tmp_words_file}"' EXIT

    while IFS= read -r sub; do
        sub="${sub//$'\r'/}"
        [[ -z "${sub}" ]] && continue
        [[ "${sub}" =~ ^[[:space:]]*# ]] && continue
        cewl -w "${tmp_words_file}" "${sub}" >/dev/null 2>&1 || true
        if [[ -s "${tmp_words_file}" ]]; then
            tr '[:upper:]' '[:lower:]' < "${tmp_words_file}" | sort -u | anew "${words_file}" || true
            : > "${tmp_words_file}"
        fi
    done < "${subs_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    cewl_wordlist_generation "$@"
fi
