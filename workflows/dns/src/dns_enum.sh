#!/usr/bin/env bash
set -euo pipefail

dns_enu() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    local notify_enabled="${3:-false}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: dns_enu <subs_file> [output_path] [notify]" >&2
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

    local dns_dir="${output_path}/dns"
    local all_dns_file="${dns_dir}/all.dns.txt"
    local txt_records_file="${dns_dir}/txt_records.dns.txt"
    local vuln_file="${dns_dir}/vulnerable.email_spoofing.dns.txt"
    local cname_file="${dns_dir}/cname_records.dns.txt"
    local new_vulns_file=""

    mkdir -p "${dns_dir}"

    new_vulns_file="$(mktemp)"
    trap '[[ -n "${new_vulns_file:-}" ]] && rm -f "${new_vulns_file}"' EXIT

    cat "${subs_file}" | \
        dnsx -silent -recon -nc -o "${all_dns_file}"

    if [[ -s "${all_dns_file}" ]]; then
        grep -E '\sTXT\s' "${all_dns_file}" | anew "${txt_records_file}" || true
        grep -E '\sCNAME\s' "${all_dns_file}" | anew "${cname_file}" || true
    fi

    if [[ -s "${txt_records_file}" ]]; then
        grep -Ei '\b(~|\?)all\b' "${txt_records_file}" | \
            grep -i 'v=spf1' | \
            anew "${vuln_file}" | tee "${new_vulns_file}" >/dev/null || true
    fi

    if [[ "${notify_enabled}" == "true" ]] && [[ -s "${new_vulns_file}" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
        {
            echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New potential email spoofing domains\n"
            cat "${new_vulns_file}"
        } | notify -bulk -provider telegram || true
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    dns_enu "$@"
fi
