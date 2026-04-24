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

def gau_enum(subs_file, output_path):
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    base_output = os.path.abspath(output_path)
    urls_dir = os.path.join(base_output, "urls")
    all_urls_file = os.path.join(urls_dir, "all.gau.urls.txt")
    
    os.makedirs(urls_dir, exist_ok=True)

    # Definimos os caminhos fora para limpeza no finally
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
            logger.warning("No valid hosts found to enumerate via gau.")
            return

        # 2. Run gau
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_urls:
            tmp_urls_path = tmp_urls.name

        logger.info(f"Starting gau enumeration for {len(seen_hosts)} hosts...")
        try:
            with open(tmp_norm_subs_path, 'r') as stdin_file:
                cmd = [
                    "gau", 
                    "--threads", "100", 
                    "--timeout", "15", 
                    "--o", tmp_urls_path
                ]
                subprocess.run(cmd, stdin=stdin_file, capture_output=True, text=True, check=False)
        except Exception as e:
            logger.error(f"Error executing gau: {e}")
            return

        # 3. Save new URLs using anew
        if os.path.exists(tmp_urls_path) and os.path.getsize(tmp_urls_path) > 0:
            logger.info("Updating master URLs file with gau results...")
            if shutil.which("anew"):
                with open(tmp_urls_path, 'r') as f:
                    subprocess.run(["anew", all_urls_file], stdin=f)
            else:
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
            logger.info("gau returned no results for the selected hosts.")

    finally:
        # Cleanup
        if tmp_norm_subs_path and os.path.exists(tmp_norm_subs_path):
            os.remove(tmp_norm_subs_path)
        if tmp_urls_path and os.path.exists(tmp_urls_path):
            os.remove(tmp_urls_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 gau_enum.py <subs_file> <output_path>")
        sys.exit(1)

    gau_enum(sys.argv[1], sys.argv[2])