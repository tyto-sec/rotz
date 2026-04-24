import os
import sys
import json
import argparse
import yaml
from pathlib import Path

def get_input(prompt, default):
    """Auxiliar para capturar input com valor padrão."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def str_to_bool(value):
    """Converte strings comuns para booleano."""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "y", "t")

def generate_config(args_map):
    """Calcula todos os caminhos baseados nas variáveis raiz."""
    root = os.path.abspath(args_map['ROOT'])
    target = args_map['TARGET']
    org = args_map['ORGANIZATION']
    
    # Dicionário final de variáveis
    vars_config = {
        "ROOT": root,
        "TARGET": target,
        "INPUT_ORGANIZATION": org,
        "INPUT_DOMAINS": f"{root}/input/{target}/domains.txt",
        
        # Subdomains
        "SUBDOMAIN_OUTPUT_PATH": f"{root}/output/{target}/subs",
        "SUBDOMAIN_OUTPUT_FILE": f"{root}/output/{target}/subs/all.subs.txt",
        "LIVE_SUBDOOMAINS_FILE": f"{root}/output/{target}/subs/all.live.subs.txt",
        "SUBDOMAIN_WORDLIST": f"{root}/wordlists/subdomains/subdomains-top1million-5000.txt",
        "SUBDOMAIN_SCRIPTS_FOLDER": f"{root}/workflows/subdomains/src",
        "SUBDOMAIN_WORKFLOWS_FOLDER": f"{root}/workflows/subdomains",
        
        # Infrastructure/IPs
        "IPS_OUTPUT_PATH": f"{root}/output/{target}/ips",
        "IPS_OUTPUT_FILE": f"{root}/output/{target}/ips/all.ips.txt",
        "INFRASTRUCTURE_SCRIPTS_FOLDER": f"{root}/workflows/infrastructure/src",
        "INFRASTRUCTURE_WORKFLOWS_FOLDER": f"{root}/workflows/infrastructure",
        
        # DNS
        "DNS_OUTPUT_PATH": f"{root}/output/{target}/dns",
        "DNS_SCRIPTS_FOLDER": f"{root}/workflows/dns/src",
        "DNS_WORKFLOWS_FOLDER": f"{root}/workflows/dns",

        # Resolution
        "SUBDOMAIN_RESOLUTION_SCRIPTS_FOLDER": f"{root}/workflows/probing/src",
        "SUBDOMAIN_RESOLUTION_WORKFLOWS_FOLDER": f"{root}/workflows/probing",

        # Content
        "CONTENT_OUTPUT_PATH": f"{root}/output/{target}/content",
        "CONTENT_SCRIPTS_FOLDER": f"{root}/workflows/content/src",
        "CONTENT_WORKFLOWS_FOLDER": f"{root}/workflows/content",
        "ALL_URLS_FILE": f"{root}/output/{target}/content/urls/all.urls.txt",
        "CLEANED_URLS_FILE": f"{root}/output/{target}/content/urls/all.cleaned.urls.txt",
        "GAU_URLS_FILE": f"{root}/output/{target}/content/urls/all.gau.urls.txt",
        "KATANA_URLS_FILE": f"{root}/output/{target}/content/urls/all.katana.urls.txt",
        "PARAMS_URLS_FILE": f"{root}/output/{target}/content/urls/all.params.urls.txt",

        # JavaScript
        "JS_OUTPUT_PATH": f"{root}/output/{target}/content/javascript",
        "JS_URLS_FILE": f"{root}/output/{target}/content/urls/all.js.urls.txt",
        "SELECTED_JS_FILES": f"{root}/output/{target}/content/javascript/all.javascript.txt",
        "JS_DOWNLOAD_FOLDER": f"{root}/output/{target}/content/javascript/downloads",
        "JS_SCRIPTS_FOLDER": f"{root}/workflows/javascript/src",
        "JS_WORKFLOWS_FOLDER": f"{root}/workflows/javascript",
        "JS_REGEX_FILE": "/opt/JSScanner/Regex.txt",

        # Fuzzing
        "FUZZING_OUTPUT_PATH": f"{root}/output/{target}/content/fuzzing",
        "GIT_OUTPUT_PATH": f"{root}/output/{target}/content/fuzzing/git",
        "CEWL_OUTPUT_PATH": f"{root}/output/{target}/content/wordlists/cewl",
        "WORDLISTS_OUTPUT_PATH": f"{root}/output/{target}/content/wordlists",
        "DIRECTORY_WORDLIST": f"{root}/wordlists/directories/fuzz-Bo0oM.txt",
        "PATH_WORDLIST": f"{root}/output/{target}/content/wordlists/all.paths.txt",
        "WORDS_WORDLIST": f"{root}/output/{target}/content/wordlists/all.words.txt",
        "FUZZING_SCRIPTS_FOLDER": f"{root}/workflows/fuzzing/src",
        "FUZZING_WORKFLOWS_FOLDER": f"{root}/workflows/fuzzing",

        # Vulns
        "VULNERABILITY_OUTPUT_PATH": f"{root}/output/{target}/content/vuln",
        "VULNERABILITY_SCRIPTS_FOLDER": f"{root}/workflows/vulns/src",
        "VULNERABILITY_WORKFLOWS_FOLDER": f"{root}/workflows/vulns",
    }

    # Adicionar Booleans (convertidos)
    bool_keys = [
        "SUBDOMAIN_NOTIFY", "SUBDOMAIN_BRUTEFORCE", "ORGANIZATION_SCAN", 
        "ORGANIZATION_NOTIFY", "DNS_NOTIFY", "SUBDOMAIN_RESOLUTION_NOTIFY",
        "CONTENT_NOTIFY", "CONTENT_ACTIVE", "JS_NOTIFY", "JS_ACTIVE",
        "JS_NUCLEI", "JS_DOWNLOAD", "FUZZING_ACTIVE", "FUZZING_NOTIFY"
    ]
    
    for key in bool_keys:
        vars_config[key] = str_to_bool(args_map.get(key, True))

    return vars_config

def main():
    parser = argparse.ArgumentParser(description="Rayders Config Generator")
    parser.add_argument("-f", "--file", help="Input JSON or YAML file with parameters")
    parser.add_argument("--root", help="Path to ROOT folder")
    parser.add_argument("--target", help="Target name (e.g. hackthissite)")
    parser.add_argument("--org", help="Organization name")
    parser.add_argument("--out", help="Save the generated YAML to this file", default="rayder_vars.yaml")
    
    args = parser.parse_args()
    data = {}

    # 1. Carregar de arquivo se existir
    if args.file:
        with open(args.file, 'r') as f:
            if args.file.endswith('.json'):
                data = json.load(f)
            else:
                data = yaml.safe_load(f)

    # 2. Interativo se não houver argumentos suficientes
    if not args.file and not (args.root and args.target):
        print("--- Rayders Configuration Setup ---")
        data['ROOT'] = get_input("Path to ROOT folder", os.getcwd())
        data['TARGET'] = get_input("Target name (slug)", "hackthissite")
        data['ORGANIZATION'] = get_input("Organization name", "HackThisSite")
        
        # Pergunta sobre as opções de ativação
        print("\n--- Boolean Options (y/n) ---")
        data['SUBDOMAIN_BRUTEFORCE'] = get_input("Enable Subdomain Bruteforce?", "y")
        data['ORGANIZATION_SCAN'] = get_input("Enable Organization Scan?", "n")
        data['CONTENT_ACTIVE'] = get_input("Enable Content Enumeration?", "y")
        data['JS_ACTIVE'] = get_input("Enable JS Analysis?", "y")
        data['FUZZING_ACTIVE'] = get_input("Enable Fuzzing?", "y")
        data['SUBDOMAIN_NOTIFY'] = get_input("Enable Notifications?", "y")
        # Preenche o restante dos bools com o valor geral de notify
        for k in ["ORGANIZATION_NOTIFY", "DNS_NOTIFY", "CONTENT_NOTIFY", "JS_NOTIFY", "FUZZING_NOTIFY"]:
            data[k] = data['SUBDOMAIN_NOTIFY']
    else:
        # Prioridade para argumentos de linha de comando
        if args.root: data['ROOT'] = args.root
        if args.target: data['TARGET'] = args.target
        if args.org: data['ORGANIZATION'] = args.org

    # 3. Gerar dicionário final
    final_vars = generate_config(data)

    # 4. Salvar YAML
    output_structure = {"vars": final_vars}
    with open(args.out, 'w') as yf:
        yaml.dump(output_structure, yf, default_flow_style=False, sort_keys=False)

    print(f"\n[+] Global variables generated successfully in: {args.out}")
    print(f"[!] You can now rub: rayder -w workflow.yaml -v {args.out}")

if __name__ == "__main__":
    main()