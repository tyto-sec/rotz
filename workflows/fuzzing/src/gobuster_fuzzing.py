import os
import subprocess
import shutil
import logging
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def process_subdomain(sub, wordlist, fuzz_dir, notify_enabled):
    """
    Processes a single subdomain using Gobuster and saves the raw output in fuzz_dir.
    """
    sub = sub.strip()
    if not sub or sub.startswith('#'):
        return

    # Ensure URL formatting
    base_url = sub if sub.startswith("http") else f"https://{sub}"
    
    # Create a safe filename for output
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', base_url)
    out_raw = os.path.join(fuzz_dir, f"gobuster.{safe_name}.txt")
    
    logger.info(f"[+] Fuzzing {base_url}...")

    # Execute Gobuster
    # Threads 20 for internal fuzzing, Following redirects enabled
    gobuster_cmd = [
        "gobuster", "dir",
        "-u", f"{base_url}/",
        "-w", wordlist,
        "-q",
        "-r",                     # FOLLOW REDIRECTS
        "--no-error",
        "-b", "404,400,500,502",  # Ignore common errors
        "-o", out_raw,
        "-t", "20",                # High concurrency per target
        "-a", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--timeout", "10s"         
    ]

    try:
        # Run the command and capture output
        subprocess.run(gobuster_cmd, capture_output=True, text=True, check=False)
        
        # Check if findings were saved
        if os.path.exists(out_raw) and os.path.getsize(out_raw) > 0:
            count = 0
            findings_summary = []
            
            with open(out_raw, 'r') as f:
                for line in f:
                    if line.strip():
                        count += 1
                        # Save a few lines for the notification summary
                        if count <= 10:
                            findings_summary.append(line.strip())

            logger.info(f"[!] Fuzzing finished for {sub}. {count} occurrences found. Saved to {out_raw}")
            
            # Notification logic
            if notify_enabled and count > 0:
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    summary_text = "\n".join(findings_summary)
                    if count > 10:
                        summary_text += f"\n... and {count - 10} more findings."
                    
                    msg = f"[{timestamp}] Gobuster finished on {sub}\nFindings: {count}\n\n{summary_text}"
                    subprocess.run(
                        ["notify", "-bulk", "-provider", "telegram"],
                        input=msg,
                        text=True,
                        capture_output=True
                    )
        else:
            logger.info(f"[-] No common directories found on {base_url}")

    except Exception as e:
        logger.error(f"Error processing {sub}: {e}")

def gobuster_fuzzing(subs_file, fuzz_dir, wordlist, notify_enabled=False):
    """
    Orchestrates Gobuster fuzzing across all subdomains.
    """
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    if not shutil.which("gobuster"):
        logger.error("Gobuster is not installed.")
        return

    # Ensure fuzzing output folder exists
    os.makedirs(fuzz_dir, exist_ok=True)

    with open(subs_file, 'r', encoding='utf-8', errors='ignore') as f:
        subdomains = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    if not subdomains:
        logger.warning("No subdomains found to fuzz.")
        return

    logger.info(f"Starting Gobuster fuzzing on {len(subdomains)} targets...")

    # Limit concurrent subdomains to 3 to optimize internal gobuster threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        for sub in subdomains:
            executor.submit(process_subdomain, sub, wordlist, fuzz_dir, notify_enabled)

if __name__ == "__main__":
    import sys
    # Usage: python3 script.py <subs_file> <fuzz_dir> <wordlist> <notify>
    if len(sys.argv) < 5:
        print("Usage: python3 gobuster_fuzzing.py <subs_file> <fuzz_dir> <wordlist> <notify>")
        sys.exit(1)

    s_file = sys.argv[1]
    f_dir = sys.argv[2]
    w_list = sys.argv[3]
    n_enab = sys.argv[4].lower() == "true"

    gobuster_fuzzing(s_file, f_dir, w_list, n_enab)