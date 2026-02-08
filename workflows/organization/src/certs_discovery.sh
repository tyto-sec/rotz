#!/usr/bin/env bash
set -euo pipefail

certs_discovery() {
	local domains_file="${1:-}"
	local output_path="${2:-${OUTPUT_PATH:-output}}"
	local notify_enabled="${3:-false}"
	if [[ -z "${domains_file}" ]]; then
		echo "Usage: certs_discovery <domains_file> [output_path]" >&2
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

	local certs_dir="${output_path}/subs/subdomains"
	local certs_file="${certs_dir}/certs.subs.txt"
	local all_certs_file="${certs_dir}/all.subs.txt"
	local new_certs_file=""
	local newly_discovered_file=""
	local first_run=false

	mkdir -p "${certs_dir}"

	if [[ ! -s "${certs_file}" ]]; then
		first_run=true
	fi

	new_certs_file="$(mktemp)"
	newly_discovered_file="$(mktemp)"
	trap '[[ -n "${new_certs_file:-}" ]] && rm -f "${new_certs_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"' EXIT

	grep -vE '^\s*#|^\s*$' "${domains_file}" | metabigor related -s "cert" | sort -u > "${new_certs_file}"

	if [[ -f "${all_certs_file}" ]]; then
		comm -13 <(sort "${all_certs_file}") <(sort "${new_certs_file}") > "${newly_discovered_file}"
	else
		cp "${new_certs_file}" "${newly_discovered_file}"
	fi

	if [[ -s "${newly_discovered_file}" ]]; then
		if [[ "${notify_enabled}" == "true" ]] && [[ "${first_run}" == "false" ]] && command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
			{
				echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Certs Domains\n"
				cat "${newly_discovered_file}"
			} | notify -bulk -provider telegram || true
		fi
		cat "${newly_discovered_file}" | anew "${all_certs_file}"
	fi

	cp "${new_certs_file}" "${certs_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	certs_discovery "$@"
fi
