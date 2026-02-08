#!/usr/bin/env bash
set -euo pipefail

github_enum() {
	local domains_file="${1:-}"
	local output_path="${2:-${OUTPUT_PATH:-output}}"
	if [[ -z "${domains_file}" ]]; then
		echo "Usage: github_enum <domains_file> [output_path]" >&2
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

	local subs_dir="${output_path}/subs/subdomains"
	local tmp_dir="${output_path}/subs/tmp"
	local subs_file="${subs_dir}/github.subs.txt"
	local all_subs_file="${subs_dir}/all.subs.txt"
	local new_subs_file=""
	local newly_discovered_file=""

	mkdir -p "${subs_dir}" "${tmp_dir}"

	new_subs_file="$(mktemp)"
	newly_discovered_file="$(mktemp)"
	trap '[[ -n "${new_subs_file:-}" ]] && rm -f "${new_subs_file}"; [[ -n "${newly_discovered_file:-}" ]] && rm -f "${newly_discovered_file}"' EXIT

	export subs_dir tmp_dir new_subs_file

	grep -vE '^\s*#|^\s*$' "${domains_file}" | \
		xargs -I@ bash -c '
			tmp_file="${tmp_dir}/@.github.temp"
			github-subdomains -d "@" -k -o "${tmp_file}" 2>/dev/null || true
			if [[ -s "${tmp_file}" ]]; then
				sed "s/\\*\\.//g; s/\\*//g" "${tmp_file}" | sort -u | \
					tee -a "${new_subs_file}" >/dev/null
			fi
			rm -f "${tmp_file}"'

	sort -u "${new_subs_file}" -o "${new_subs_file}"

	if [[ -f "${subs_file}" ]]; then
		comm -13 <(sort "${subs_file}") <(sort "${new_subs_file}") > "${newly_discovered_file}"
	else
		cp "${new_subs_file}" "${newly_discovered_file}"
	fi

	if [[ -s "${newly_discovered_file}" ]]; then
		if command -v notify >/dev/null 2>&1 && [[ -f "${HOME}/.config/notify/provider-config.yaml" ]]; then
			{
				echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] New Subdomains (GitHub)\n"
				cat "${newly_discovered_file}"
			} | notify -bulk -provider telegram || true
		fi
		cat "${newly_discovered_file}" | anew "${all_subs_file}"
	fi

	cp "${new_subs_file}" "${subs_file}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	github_enum "$@"
fi
