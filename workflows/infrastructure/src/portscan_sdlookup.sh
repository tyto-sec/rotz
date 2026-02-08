#!/usr/bin/env bash
set -euo pipefail

portscan_sdlookup() {
    local ips_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${3:-false}"
    if [[ -z "${ips_file}" ]]; then
        echo "Usage: portscan_sdlookup <ips_file> [output_path] [notify]" >&2
        return 1
    fi
    if [[ ! -f "${ips_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${ips_file}" ]]; then
            ips_file="${repo_root}/${ips_file}"
        else
            echo "IPs file not found: ${ips_file}" >&2
            return 1
        fi
    fi

    local ips_dir="${output_path}/ips"
    local scans_dir="${ips_dir}/scans"
    mkdir -p "${scans_dir}"

    while IFS= read -r ip; do
        ip="${ip//$'\r'/}"
        [[ -z "${ip}" ]] && continue
        [[ "${ip}" =~ ^[[:space:]]*# ]] && continue
        sdlookup -json <<< "${ip}" > "${scans_dir}/${ip}.scan.json"

        if [[ "${notify_enabled}" == "true" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
            if python3 - <<'PY' "${scans_dir}/${ip}.scan.json" >/dev/null 2>&1; then
import json
import sys

path = sys.argv[1]
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    data = json.load(f)

vulns = data.get('vulns') or []
ports = data.get('ports') or []
unusual_ports = [p for p in ports if p not in (80, 443)]

sys.exit(0 if (len(vulns) > 0 or len(unusual_ports) > 0) else 1)
PY
                {
                    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] SDLookup findings\n"
                    cat "${scans_dir}/${ip}.scan.json"
                } | notify -bulk -provider telegram || true
            fi
        fi
    done < "${ips_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    portscan_sdlookup "$@"
fi
