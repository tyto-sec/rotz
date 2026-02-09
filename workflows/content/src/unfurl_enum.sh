#!/usr/bin/env bash
set -euo pipefail

unfurl_enum() {
    local output_path="${1:-${OUTPUT_PATH:-output}}"

    local urls_dir="${output_path}/content/urls"
    local params_dir="${output_path}/content/wordlists"
    local all_subs_file="${output_path}/subs/all.subs.txt"

    mkdir -p "${params_dir}"

    if [[ -f "${urls_dir}/all.urls.txt" ]]; then
        cat "${urls_dir}/all.urls.txt" | unfurl -u keys | anew "${params_dir}/all.keys.txt" || true
        cat "${urls_dir}/all.urls.txt" | unfurl -u values | anew "${params_dir}/all.values.txt" || true
        cat "${urls_dir}/all.urls.txt" | unfurl -u keypairs | anew "${params_dir}/all.keypairs.txt" || true
        cat "${urls_dir}/all.urls.txt" | unfurl -u domains | anew "${params_dir}/all.domains.txt" || true
        cat "${urls_dir}/all.urls.txt" | unfurl -u apexes | anew "${params_dir}/all.apex.txt" || true
        cat "${urls_dir}/all.urls.txt" | unfurl -u paths | anew "${params_dir}/all.paths.txt" || true
    fi

    if [[ -f "${urls_dir}/all.paramspider.urls.txt" ]]; then
        cat "${urls_dir}/all.paramspider.urls.txt" | unfurl -u keys | anew "${params_dir}/all.keys.txt" || true
        cat "${urls_dir}/all.paramspider.urls.txt" | unfurl -u paths | anew "${params_dir}/all.paths.txt" || true
        cat "${urls_dir}/all.paramspider.urls.txt" | unfurl -u domains | anew "${params_dir}/all.domains.txt" || true
        cat "${urls_dir}/all.paramspider.urls.txt" | unfurl -u apexes | anew "${params_dir}/all.apex.txt" || true
        cat "${urls_dir}/all.paramspider.urls.txt" | unfurl -u values | anew "${params_dir}/all.values.txt" || true
        cat "${urls_dir}/all.paramspider.urls.txt" | unfurl -u keypairs | anew "${params_dir}/all.keypairs.txt" || true
    fi

    if [[ -f "${urls_dir}/all.arjun.urls.txt" ]]; then
        cat "${urls_dir}/all.arjun.urls.txt" | unfurl -u keys | anew "${params_dir}/all.keys.txt" || true
        cat "${urls_dir}/all.arjun.urls.txt" | unfurl -u paths | anew "${params_dir}/all.paths.txt" || true
        cat "${urls_dir}/all.arjun.urls.txt" | unfurl -u domains | anew "${params_dir}/all.domains.txt" || true
        cat "${urls_dir}/all.arjun.urls.txt" | unfurl -u apexes | anew "${params_dir}/all.apex.txt" || true
        cat "${urls_dir}/all.arjun.urls.txt" | unfurl -u values | anew "${params_dir}/all.values.txt" || true
        cat "${urls_dir}/all.arjun.urls.txt" | unfurl -u keypairs | anew "${params_dir}/all.keypairs.txt" || true
    fi

    if [[ -f "${params_dir}/all.domains.txt" ]]; then
        cat "${params_dir}/all.domains.txt" | anew "${all_subs_file}" || true
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    unfurl_enum "$@"
fi
