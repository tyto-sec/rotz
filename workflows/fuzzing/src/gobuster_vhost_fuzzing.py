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

def process_vhost(sub, wordlist, fuzz_dir, notify_enabled):
    """
    Processes a single subdomain to find VHOSTs using Gobuster.
    Saves raw output and sends notifications for findings.
    """
    sub = sub.strip()
    if not sub or sub.startswith('#'):
        return

    # Ensure URL formatting
    base_url = sub if sub.startswith("http") else f"https://{sub}"
    
    # Create a safe filename for output: e.g., gobuster.vhost.sub_domain_com.txt
    host_part = re.sub(r'^https?://', '', base_url)
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', host_part)
    out_raw = os.path.join(fuzz_dir, f"gobuster.vhost.{safe_name}.txt")
    
    logger.info(f"[+] VHOST fuzzing {base_url}...")

    # Execute Gobuster vhost
    # --append-domain: crucial for finding sub-vhosts
    gobuster_cmd = [
        "gobuster", "vhost",
        "-u", base_url,
        "-w", wordlist,
        "--append-domain",
        "-q",
        "--no-error",
        "-t", "20",
        "-a", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "--timeout", "10s",
        "-o", out_raw
    ]

    try:
        subprocess.run(gobuster_cmd, capture_output=True, text=True, check=False)
        
        if os.path.exists(out_raw) and os.path.getsize(out_raw) > 0:
            count = 0
            findings_summary = []
            
            # Read findings for summary
            with open(out_raw, 'r') as f:
                for line in f:
                    if "Found:" in line or line.strip():
                        count += 1
                        if count <= 10:
                            findings_summary.append(line.strip())

            logger.info(f"[!] VHOST discovery finished for {sub}. {count} found. Saved to {out_raw}")
            
            # Notification logic
            if notify_enabled and count > 0:
                if shutil.which("notify"):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    summary_text = "\n".join(findings_summary)
                    if count > 10:
                        summary_text += f"\n... and {count - 10} more vhosts."
                    
                    msg = f"[{timestamp}] Gobuster VHOST discovery on {sub}\nTotal found: {count}\n\n{summary_text}"
                    subprocess.run(
                        ["notify", "-bulk", "-provider", "telegram"],
                        input=msg,
                        text=True,
                        capture_output=True
                    )
        else:
            logger.info(f"[-] No VHOSTs discovered on {base_url}")

    except Exception as e:
        logger.error(f"Error fuzzing VHOSTs for {sub}: {e}")

def gobuster_vhost_fuzzing(subs_file, fuzz_dir, wordlist, notify_enabled=False):
    """
    Orchestrates Gobuster VHOST fuzzing across subdomains.
    """
    if not os.path.isfile(subs_file):
        logger.error(f"Input file not found: {subs_file}")
        return

    if not shutil.which("gobuster"):
        logger.error("Gobuster is not installed.")
        return

    os.makedirs(fuzz_dir, exist_ok=True)

    with open(subs_file, 'r', encoding='utf-8', errors='ignore') as f:
        targets = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    if not targets:
        logger.warning("No targets found in the provided list.")
        return

    logger.info(f"Starting VHOST fuzzing on {len(targets)} targets...")

    # Processing targets in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        for t in targets:
            executor.submit(process_vhost, t, wordlist, fuzz_dir, notify_enabled)

if __name__ == "__main__":
    import sys
    # Usage: python3 gobuster_vhost_fuzzing.py <subs_file> <fuzz_dir> <wordlist> <notify>
    if len(sys.argv) < 5:
        print("Usage: python3 gobuster_vhost_fuzzing.py <subs_file> <fuzz_dir> <wordlist> <notify>")
        sys.exit(1)

    s_file = sys.argv[1]
    f_dir = sys.argv[2]
    w_list = sys.argv[3]
    n_enab = sys.argv[4].lower() == "true"

    gobuster_vhost_fuzzing(s_file, f_dir, w_list, n_enab)