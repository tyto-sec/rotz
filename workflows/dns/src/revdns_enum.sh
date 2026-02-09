#!/usr/bin/env bash
set -euo pipefail

revdns_enum() {
    local ips_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${3:-false}"

    if [[ -z "${ips_file}" ]]; then
        echo "Usage: revdns_enum <ips_file> [output_path] [notify]" >&2
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

    local dns_dir="${output_path}/dns"
    local subs_dir="${output_path}/subs"
    local all_subs_file="${output_path}/subs/all.subs.txt"
    local revdns_lookup_file="${dns_dir}/revdns.ip.lookup.txt"
    local revdns_domains_file="${subs_dir}/revdns.domains.txt"
    local new_domains_file=""
    local newly_discovered_file=""
    local first_run=false

    mkdir -p "${dns_dir}" "${subs_dir}"

    if [[ ! -s "${revdns_domains_file}" ]]; then
        first_run=true
    fi

    new_domains_file="$(mktemp)"
    newly_discovered_file="$(mktemp)"
    trap '[[ -n "${new_domains_file:-}" ]] && rm -f "${new_domains_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"' EXIT

    cat "${ips_file}" | \
        hakrevdns -r 1.1.1.1 | \
        anew "${revdns_lookup_file}"

    if [[ -s "${revdns_lookup_file}" ]]; then
        cat "${revdns_lookup_file}" | \
            awk '{print $2}' | \
            sed 's/\.$//' | \
            cut -d. -f1- | \
            sort -u > "${new_domains_file}"

        if [[ -f "${revdns_domains_file}" ]]; then
            comm -13 <(sort "${revdns_domains_file}") <(sort "${new_domains_file}") > "${newly_discovered_file}"
        else
            cp "${new_domains_file}" "${newly_discovered_file}"
        fi

        if [[ -s "${newly_discovered_file}" ]]; then
            if [[ "${notify_enabled}" == "true" ]] && [[ "${first_run}" == "false" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
                {
                    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Subdomains (Reverse DNS)\n"
                    cat "${newly_discovered_file}"
                } | notify -bulk -provider telegram || true
            fi
            cat "${newly_discovered_file}" | anew "${revdns_domains_file}" | anew "${all_subs_file}"
        fi
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    revdns_enum "$@"
fi
