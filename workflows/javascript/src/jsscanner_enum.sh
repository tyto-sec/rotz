#!/usr/bin/env bash
set -euo pipefail

jsscanner_enum() {
    local input_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local regex_file="${3:-/opt/JSScanner/Regex.txt}"

    if [[ -z "${input_file}" ]]; then
        echo "Usage: jsscanner_enum <input_file> [output_path] [regex_file]" >&2
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

    if [[ ! -f "${regex_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${regex_file}" ]]; then
            regex_file="${repo_root}/${regex_file}"
        elif [[ -f "/opt/JSScanner/regex.txt" ]]; then
            regex_file="/opt/JSScanner/regex.txt"
        else
            echo "Regex file not found: ${regex_file}" >&2
            return 1
        fi
    fi

    input_file="$(python3 - <<'PY' "${input_file}"
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
    )"

    regex_file="$(python3 - <<'PY' "${regex_file}"
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
    )"

    if [[ ! -f "${input_file}" ]]; then
        echo "Input file not found: ${input_file}" >&2
        return 1
    fi

    if [[ ! -f "${regex_file}" ]]; then
        echo "Regex file not found: ${regex_file}" >&2
        return 1
    fi

    output_path="$(python3 - <<'PY' "${output_path}"
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
    )"

    local js_dir="${output_path}/content/javascript"
    local output_file="${js_dir}/output.txt"
    local content_file="${js_dir}/jsscanner.content.txt"

    mkdir -p "${js_dir}"
    if [[ ! -f "/opt/JSScanner/JSScanner.py" ]]; then
        echo "JSScanner not found at /opt/JSScanner/JSScanner.py" >&2
        return 1
    fi

    local work_dir
    work_dir="$(mktemp -d)"
    trap '[[ -n "${work_dir:-}" ]] && rm -rf "${work_dir}"' EXIT

    pushd "${work_dir}" >/dev/null
    printf '%s\n%s\n' "${input_file}" "${regex_file}" | python3 /opt/JSScanner/JSScanner.py > "${content_file}" 2>&1 || true
    if [[ -f "output.txt" ]]; then
        mv "output.txt" "${output_file}"
    fi
    popd >/dev/null
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    jsscanner_enum "$@"
fi
