import os
import subprocess
import shutil
import logging
from urllib.parse import urlparse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def cewl_wordlist_generation(subs_file, output_path):
    """
    Runs CeWL on each subdomain and saves a unique wordlist for each one
    in the specified CEWL_OUTPUT_PATH.
    """
    
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    # Directory setup based on YAML: CEWL_OUTPUT_PATH
    cewl_dir = os.path.abspath(output_path)
    os.makedirs(cewl_dir, exist_ok=True)

    # Check for CeWL installation
    if not shutil.which("cewl"):
        logger.error("CeWL is not installed or not in PATH.")
        return

    logger.info(f"Starting CeWL wordlist generation for subdomains in: {subs_file}")

    try:
        with open(subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subdomains = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        for sub in subdomains:
            # Prepare the target URL
            url = sub
            if not url.startswith("http"):
                url = f"https://{sub}"
            
            # Create a clean filename for the wordlist (e.g., blog.tesla.com.txt)
            parsed_url = urlparse(url)
            host = parsed_url.netloc if parsed_url.netloc else sub
            wordlist_name = f"{host.replace(':', '_')}.txt"
            target_wordlist_path = os.path.join(cewl_dir, wordlist_name)

            logger.info(f"Generating wordlist for: {url}")
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            # Run CeWL
            # -w: write to file
            # -m 3: minimum word length
            # --lowercase: auto convert to lowercase
            cmd = [
                "cewl",
                "-w", target_wordlist_path,
                "-m", "3",
                "--lowercase",
                "-u", ua,
                url
            ]
            
            # Execute CeWL
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0 and os.path.exists(target_wordlist_path):
                # Optionally sort the file to ensure uniqueness and order
                if os.path.getsize(target_wordlist_path) > 0:
                    with open(target_wordlist_path, 'r') as wl_in:
                        words = sorted(set(wl_in.read().splitlines()))
                    with open(target_wordlist_path, 'w') as wl_out:
                        wl_out.write("\n".join(words) + "\n")
                    logger.info(f"Saved {len(words)} words to {wordlist_name}")
                else:
                    logger.warning(f"CeWL finished but the resulting wordlist for {sub} is empty.")
                    if os.path.exists(target_wordlist_path):
                        os.remove(target_wordlist_path)
            else:
                logger.error(f"CeWL failed for {url}. Error: {result.stderr.strip()}")

    except Exception as e:
        logger.error(f"Error during CeWL wordlist generation: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML vars: 
    # python3 cewl_wordlist_generation.py "{{LIVE_SUBDOOMAINS_FILE}}" "{{CEWL_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 cewl_wordlist_generation.py <subs_file> <cewl_output_path>")
        sys.exit(1)

    subs_input = sys.argv[1]
    cewl_output = sys.argv[2]

    cewl_wordlist_generation(subs_input, cewl_output)