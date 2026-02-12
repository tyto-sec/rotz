#!/usr/bin/env bash
set -euo pipefail

revdns_enum() {
    local ips_file="${1:-}"
    local domains_file_arg="${2:-}"     # new: path to domains.txt (optional)
    local output_path="${3:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${4:-false}"

    # make repo_root available for domains path resolution
    local script_dir repo_root
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    repo_root="$(cd "${script_dir}/../../.." && pwd)"

    if [[ -z "${ips_file}" ]]; then
        echo "Usage: revdns_enum <ips_file> [domains_file] [output_path] [notify]" >&2
        return 1
    fi

    if [[ ! -f "${ips_file}" ]]; then
        if [[ -f "${repo_root}/${ips_file}" ]]; then
            ips_file="${repo_root}/${ips_file}"
        else
            echo "IPs file not found: ${ips_file}" >&2
            return 1
        fi
    fi

    # Resolve domains file: prefer argument, fallback to repo_root/input/vuln/domains.txt
    local domains_file=""
    if [[ -n "${domains_file_arg}" && -f "${domains_file_arg}" ]]; then
        domains_file="${domains_file_arg}"
    elif [[ -f "${repo_root}/input/vuln/domains.txt" ]]; then
        domains_file="${repo_root}/input/vuln/domains.txt"
    else
        domains_file=""
    fi

    local dns_dir="${output_path}/dns"
    local subs_dir="${output_path}/subs"
    local all_subs_file="${output_path}/subs/all.subs.txt"
    local revdns_lookup_file="${dns_dir}/revdns.ip.lookup.txt"
    local revdns_domains_file="${subs_dir}/revdns.domains.txt"
    local new_domains_file=""
    local newly_discovered_file=""
    local filtered_newly=""
    local first_run=false

    mkdir -p "${dns_dir}" "${subs_dir}"

    if [[ ! -s "${revdns_domains_file}" ]]; then
        first_run=true
    fi

    new_domains_file="$(mktemp)"
    newly_discovered_file="$(mktemp)"
    filtered_newly="$(mktemp)"
    trap '[[ -n "${new_domains_file:-}" ]] && rm -f "${new_domains_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"; [[ -n "${filtered_newly:-}" ]] && rm -f "${filtered_newly}"' EXIT

    cat "${ips_file}" | \
        hakrevdns -r 1.1.1.1 | \
        anew "${revdns_lookup_file}"

    if [[ -s "${revdns_lookup_file}" ]]; then
        awk '{print $2}' "${revdns_lookup_file}" | \
            sed 's/\.$//' | \
            cut -d. -f1- | \
            sort -u > "${new_domains_file}"

        if [[ -f "${revdns_domains_file}" ]]; then
            comm -13 <(sort "${revdns_domains_file}") <(sort "${new_domains_file}") > "${newly_discovered_file}"
        else
            cp "${new_domains_file}" "${newly_discovered_file}"
        fi

        if [[ -s "${newly_discovered_file}" ]]; then
            # If domains_file is set, filter newly discovered to only lines containing any substring from domains_file
            if [[ -n "${domains_file}" ]]; then
                grep -F -f "${domains_file}" "${newly_discovered_file}" > "${filtered_newly}" || true
            else
                cp "${newly_discovered_file}" "${filtered_newly}"
            fi

            if [[ -s "${filtered_newly}" ]]; then
                if [[ "${notify_enabled}" == "true" ]] && [[ "${first_run}" == "false" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
                    {
                        echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Subdomains (Reverse DNS)\n"
                        cat "${filtered_newly}"
                    } | notify -bulk -provider telegram || true
                fi

                # append ALL newly discovered to revdns_domains_file, but only filtered results to all_subs_file
                sort -u "${newly_discovered_file}" | anew "${revdns_domains_file}" >/dev/null || true
                sort -u "${filtered_newly}" | anew "${all_subs_file}" >/dev/null || true
            fi
        fi
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    revdns_enum "$@"
fi