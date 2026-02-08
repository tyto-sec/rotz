#!/usr/bin/env bash
set -euo pipefail

asn_discovery() {
    local organization="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"
    if [[ -z "${organization}" ]]; then
        echo "Usage: asn_discovery <organization> [output_path]" >&2
        return 1
    fi

    local ips_dir="${output_path}/ips"
    local asn_ips_file="${ips_dir}/asn.ips.txt"
    local all_ips_file="${ips_dir}/all.ips.txt"
    local new_asn_ips_file=""
    local newly_discovered_file=""

    mkdir -p "${ips_dir}"

    new_asn_ips_file="$(mktemp)"
    newly_discovered_file="$(mktemp)"
    trap '[[ -n "${new_asn_ips_file:-}" ]] && rm -f "${new_asn_ips_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"' EXIT

    echo "${organization}" | \
        metabigor net --org -v | \
        awk '{print $3}' | \
        sed 's/[[0-9]]\+\.//g' | \
        python3 -c 'import ipaddress,sys
for line in sys.stdin:
    cidr = line.strip()
    if not cidr:
        continue
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        continue
    if net.version != 4:
        continue
    for ip in net:
        print(ip)' | \
        sort -u > "${new_asn_ips_file}"

    if [[ -f "${asn_ips_file}" ]]; then
        comm -13 <(sort "${asn_ips_file}") <(sort "${new_asn_ips_file}") > "${newly_discovered_file}"
    else
        cp "${new_asn_ips_file}" "${newly_discovered_file}"
    fi

    if [[ -s "${newly_discovered_file}" ]]; then
        # {
        #     echo "[$(date '+%Y-%m-%d %H:%M:%S')] New ASN IPs"
        #     cat "${newly_discovered_file}"
        # } | notify -bulk -provider telegram
        cat "${newly_discovered_file}" | anew "${all_ips_file}"
    fi

    cp "${new_asn_ips_file}" "${asn_ips_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    asn_discovery "$@"
fi