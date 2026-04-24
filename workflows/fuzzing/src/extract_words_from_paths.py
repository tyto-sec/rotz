import os
import re
import shutil
import logging
import subprocess

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def is_valid_word(token):
    """
    Aplica os filtros de sanitização:
    1. Deve iniciar com letra (a-z) ou ponto (.)
    2. Deve terminar com letra (a-z) ou número (0-9)
    3. Não pode ser um arquivo (extensões como .js, .php, etc)
    4. Não pode ser apenas um número (inteiro ou double)
    """
    # Filtro de Início: Deve começar com [a-zA-Z] ou .
    if not re.match(r'^[a-zA-Z0-9\.]', token):
        return False

    # Filtro de Fim: Deve terminar com [a-zA-Z0-9]
    if not re.search(r'[a-zA-Z0-9]$', token):
        return False

    # Filtro de Arquivo: Ignora se parecer um arquivo (ex: index.php, style.css)
    if bool(re.search(r'\.[a-zA-Z0-9]{2,4}$', token)):
        return False

    # Filtro Numérico: Ignora se for apenas um número (Integer ou Double)
    if bool(re.match(r'^-?[0-9]+(\.[0-9]+)?$', token)):
        return False
    
    # Filtro de Lixo: Ignora strings muito longas com muitos números (ID/Hashes)
    if len(token) > 10 and bool(re.search(r'[0-9]{5,}', token)):
        return False

    return True

def extract_words_from_paths(paths_file, output_path):
    if not os.path.isfile(paths_file):
        logger.error(f"Paths file not found: {paths_file}")
        return

    wordlists_dir = os.path.abspath(output_path)
    words_file = os.path.join(wordlists_dir, "paths.word.list")
    
    os.makedirs(wordlists_dir, exist_ok=True)

    logger.info(f"Extracting strictly formatted keywords from: {paths_file}")

    try:
        words = set()
        
        with open(paths_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Remove Query e Fragmentos, limpa as barras
                line = line.split('?')[0].split('#')[0].replace('/', ' ')
                
                # Tokenização baseada em espaços e caracteres especiais
                tokens = re.split(r"[^a-zA-Z0-9._-]+", line)
                
                for token in tokens:
                    token = token.strip()
                    
                    # Filtro de comprimento mínimo e regras customizadas
                    if token and len(token) >= 2:
                        if is_valid_word(token):
                            words.add(token.lower())

        if words:
            logger.info(f"Extracted {len(words)} unique valid keywords.")
            output_content = "\n".join(sorted(words)) + "\n"
            
            if shutil.which("anew"):
                subprocess.run(["anew", words_file], input=output_content, text=True, capture_output=True)
            else:
                existing = set()
                if os.path.exists(words_file):
                    with open(words_file, 'r') as f:
                        existing = set(l.strip() for l in f if l.strip())
                
                truly_new = [w for w in words if w not in existing]
                if truly_new:
                    with open(words_file, 'a') as f:
                        f.write("\n".join(sorted(truly_new)) + "\n")
            
            logger.info(f"Updated wordlist: {words_file}")
        else:
            logger.info("No words matching the strict criteria were found.")

    except Exception as e:
        logger.error(f"Error during word extraction: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 extract_words_from_paths.py <paths_file> <output_path>")
        sys.exit(1)

    extract_words_from_paths(sys.argv[1], sys.argv[2])