#!/usr/bin/env bash
set -euo pipefail

google_analytics_discovery() {
	local domains_file="${1:-}"
	local output_path="${2:-${OUTPUT_PATH:-output}}"
	if [[ -z "${domains_file}" ]]; then
		echo "Usage: google_analytics_discovery <domains_file> [output_path]" >&2
		return 1
	fi
	if [[ ! -f "${domains_file}" ]]; then
		local script_dir
		local repo_root
		script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
		repo_root="$(cd "${script_dir}/../../.." && pwd)"
		if [[ -f "${repo_root}/${domains_file}" ]]; then
			domains_file="${repo_root}/${domains_file}"
		else
			echo "Domains file not found: ${domains_file}" >&2
			return 1
		fi
	fi

	local ga_dir="${output_path}/subs/subdomains"
	local ga_file="${ga_dir}/google-analytics.subs.txt"
	local all_ga_file="${ga_dir}/all.subs.txt"
	local new_ga_file=""
	local newly_discovered_file=""

	mkdir -p "${ga_dir}"

	new_ga_file="$(mktemp)"
	newly_discovered_file="$(mktemp)"
	trap '[[ -n "${new_ga_file:-}" ]] && rm -f "${new_ga_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"' EXIT

	grep -vE '^\s*#|^\s*$' "${domains_file}" | metabigor related -s "google-analytic" | sort -u > "${new_ga_file}"

	if [[ -f "${ga_file}" ]]; then
		comm -13 <(sort "${ga_file}") <(sort "${new_ga_file}") > "${newly_discovered_file}"
	else
		cp "${new_ga_file}" "${newly_discovered_file}"
	fi

	if [[ -s "${newly_discovered_file}" ]]; then
		if command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
			{
				echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Google Analytics Domains\n"
				cat "${newly_discovered_file}"
			} | notify -bulk -provider telegram || true
		fi
		cat "${newly_discovered_file}" | anew "${all_ga_file}"
	fi

	cp "${new_ga_file}" "${ga_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	google_analytics_discovery "$@"
fi
