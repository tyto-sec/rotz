import os
import subprocess
import shutil
import tempfile
import logging
from urllib.parse import urlparse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def normalize_host(line: str) -> str:
    """Helper to extract clean hostname from a string or URL."""
    line = line.strip()
    if not line or line.startswith('#'):
        return ""
    if line.startswith("//"):
        line = "http:" + line
    if "://" not in line:
        return line.rstrip('.').lower()
    try:
        parsed = urlparse(line)
        host = (parsed.hostname or "").rstrip('.').lower()
        return host
    except Exception:
        return ""

def katana_enum(subs_file, output_path):
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    # Directory setup based on YAML: CONTENT_OUTPUT_PATH
    base_output = os.path.abspath(output_path)
    urls_dir = os.path.join(base_output, "urls")
    all_urls_file = os.path.join(urls_dir, "all.katana.urls.txt")
    
    os.makedirs(urls_dir, exist_ok=True)

    tmp_urls_path = None
    tmp_norm_subs_path = None

    try:
        # 1. Normalize subdomains inside the temp file context
        seen_hosts = set()
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_norm_subs:
            tmp_norm_subs_path = tmp_norm_subs.name
            logger.info(f"Normalizing subdomains from: {subs_file}")
            
            with open(subs_file, 'r', encoding='utf-8', errors='ignore') as fin:
                for line in fin:
                    host = normalize_host(line)
                    if host and host not in seen_hosts:
                        seen_hosts.add(host)
                        tmp_norm_subs.write(host + "\n")
            
            tmp_norm_subs.flush()

        if not seen_hosts:
            logger.warning("No valid hosts found to crawl via Katana.")
            return

        # 2. Prepare temp file for Katana output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_urls:
            tmp_urls_path = tmp_urls.name

        # 3. Run Katana
        logger.info(f"Starting Katana crawling for {len(seen_hosts)} hosts...")
        try:
            with open(tmp_norm_subs_path, 'r') as stdin_file:
                # katana parameters based on bash script: -c 2 -p 2 -rd 1 -rl 30
                cmd = [
                        "katana",
                        "-c", "30",    # Concurrent workers
                        "-p", "15",    # Parallelism (lowered for stability per host)
                        "-d", "3",     # Depth lowered to 3 (Crucial for speed)
                        "-rl", "200",   # Higher Rate Limit (if server allows)
                        "-jc",         # JS Crawling (Keep enabled)
                        "-kf", "all",  # Known Files 
                        "-aff",        # Automatic Form Fill
                        "-silent",
                        "-ct", "15s",  # Crawl Timeout: Don't spend more than 15m on a site
                        "-mrs", "1000" # Max Resource Size: Skip files larger than 1MB
                    ]
                
                # We execute the process and write stdout to our temp file
                with open(tmp_urls_path, 'w') as out_f:
                    subprocess.run(cmd, stdin=stdin_file, stdout=out_f, stderr=subprocess.PIPE, text=True, check=False)
                    
        except Exception as e:
            logger.error(f"Error executing Katana: {e}")
            return

        # 4. Save new URLs using anew
        if os.path.exists(tmp_urls_path) and os.path.getsize(tmp_urls_path) > 0:
            logger.info("Updating master URLs file with Katana results...")
            if shutil.which("anew"):
                with open(tmp_urls_path, 'r') as f:
                    subprocess.run(["anew", all_urls_file], stdin=f)
            else:
                # Fallback Logic
                with open(tmp_urls_path, 'r') as f:
                    new_urls = set(l.strip() for l in f if l.strip())
                
                existing_urls = set()
                if os.path.exists(all_urls_file):
                    with open(all_urls_file, 'r') as f:
                        existing_urls = set(l.strip() for l in f if l.strip())
                
                truly_new = [url for url in new_urls if url not in existing_urls]
                if truly_new:
                    with open(all_urls_file, 'a') as f:
                        f.write("\n".join(truly_new) + "\n")
        else:
            logger.info("Katana returned no results.")

    finally:
        # Cleanup
        if tmp_norm_subs_path and os.path.exists(tmp_norm_subs_path):
            os.remove(tmp_norm_subs_path)
        if tmp_urls_path and os.path.exists(tmp_urls_path):
            os.remove(tmp_urls_path)

if __name__ == "__main__":
    import sys
    # Usage: python3 katana_enum.py "{{LIVE_SUBDOOMAINS_FILE}}" "{{CONTENT_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 katana_enum.py <subs_file> <output_path>")
        sys.exit(1)

    katana_enum(sys.argv[1], sys.argv[2])