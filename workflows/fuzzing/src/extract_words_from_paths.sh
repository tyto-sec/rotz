#!/usr/bin/env bash
set -euo pipefail

extract_words_from_paths() {
    local paths_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${paths_file}" ]]; then
        echo "Usage: extract_words_from_paths <paths_file> [output_path]" >&2
        return 1
    fi

    if [[ ! -f "${paths_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${paths_file}" ]]; then
            paths_file="${repo_root}/${paths_file}"
        else
            echo "Paths file not found: ${paths_file}" >&2
            return 1
        fi
    fi

    local fuzz_dir="${output_path}/content/wordlists"
    local words_file="${fuzz_dir}/paths.word.list"
    local tmp_words_file=""

    mkdir -p "${fuzz_dir}"

    tmp_words_file="$(mktemp)"
    trap '[[ -n "${tmp_words_file:-}" ]] && rm -f "${tmp_words_file}"' EXIT

    python3 - "${paths_file}" "${tmp_words_file}" <<'PY'
import re
import sys

in_path, out_path = sys.argv[1:3]
words = set()

with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        line = line.replace('/', ' ')
        tokens = re.split(r"[^A-Za-z0-9._-]+", line)
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            words.add(token.lower())

with open(out_path, 'w', encoding='utf-8') as out:
    for word in sorted(words):
        out.write(word + "\n")
PY

    if [[ -s "${tmp_words_file}" ]]; then
        cat "${tmp_words_file}" | anew "${words_file}" || true
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    extract_words_from_paths "$@"
fi
