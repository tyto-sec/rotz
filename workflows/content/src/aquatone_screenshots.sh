#!/usr/bin/env bash
# Removemos o -e ou tratamos o comando especificamente
set -uo pipefail 

aquatone_screenshots() {
    local subs_file="${1:-}"
    local output_path="${2:-${OUTPUT_PATH:-output}}"

    if [[ -z "${subs_file}" ]]; then
        echo "Usage: aquatone_screenshots <subs_file> [output_path]" >&2
        return 1
    fi

    # ... (manteve a lógica de busca do arquivo) ...
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

    local screenshots_dir="${output_path}/content/screenshots/aquatone"
    mkdir -p "${screenshots_dir}"

    # Adicionamos "|| true" ao final para garantir que o exit code seja sempre 0
    cat "${subs_file}" | \
        aquatone -out "${screenshots_dir}" -scan-timeout 5000 -http-timeout 5000 -threads 200 || echo "Aquatone finalizou com erros, mas continuando workflow..."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    aquatone_screenshots "$@"
    # Força saída com sucesso para o orquestrador (YAML) não parar
    exit 0
fi