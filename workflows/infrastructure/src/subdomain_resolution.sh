#!/usr/bin/env bash
set -euo pipefail

subdomain_resolution() {
    local subdomains_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${3:-false}"
    if [[ -z "${subdomains_file}" ]]; then
        echo "Usage: subdomain_resolution <subdomains_file> [output_path] [notify]" >&2
        return 1
    fi
    if [[ ! -f "${subdomains_file}" ]]; then
        local script_dir
        local repo_root
        script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        repo_root="$(cd "${script_dir}/../../.." && pwd)"
        if [[ -f "${repo_root}/${subdomains_file}" ]]; then
            subdomains_file="${repo_root}/${subdomains_file}"
        else
            echo "Subdomains file not found: ${subdomains_file}" >&2
            return 1
        fi
    fi

    local ips_dir="${output_path}/ips"
    local resolved_ips_file="${ips_dir}/subdomains.resolved.ips.txt"
    local all_ips_file="${ips_dir}/all.ips.txt"
    local new_ips_file=""
    local newly_discovered_file=""
    local first_run=false

    mkdir -p "${ips_dir}"

    if [[ ! -s "${resolved_ips_file}" ]]; then
        first_run=true
    fi

    new_ips_file="$(mktemp)"
    newly_discovered_file="$(mktemp)"
    trap '[[ -n "${new_ips_file:-}" ]] && rm -f "${new_ips_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"' EXIT

    grep -vE '^\s*#|^\s*$' "${subdomains_file}" | \
        httpx -ip -silent | \
        awk -F'[][]' 'NF>=2 {print $2}' | \
        sort -u > "${new_ips_file}"

    if [[ -f "${all_ips_file}" ]]; then
        comm -13 <(sort "${all_ips_file}") <(sort "${new_ips_file}") > "${newly_discovered_file}"
    else
        cp "${new_ips_file}" "${newly_discovered_file}"
    fi

    if [[ -s "${newly_discovered_file}" ]]; then
        if [[ "${notify_enabled}" == "true" ]] && [[ "${first_run}" == "false" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
            {
                echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Subdomain IPs\n"
                cat "${newly_discovered_file}"
            } | notify -bulk -provider telegram || true
        fi
        cat "${newly_discovered_file}" | anew "${all_ips_file}"
        cat "${newly_discovered_file}" | anew "${resolved_ips_file}"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    subdomain_resolution "$@"
fi
