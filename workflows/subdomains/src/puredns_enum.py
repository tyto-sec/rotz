import os
import subprocess
import shutil
import tempfile
import logging
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def puredns_enum(domains_file, output_path, notify_enabled=False, wordlist_file=None):
    if not os.path.isfile(domains_file):
        logger.error(f"Domains file not found: {domains_file}")
        return

    if wordlist_file is None or not os.path.isfile(wordlist_file):
        logger.error(f"Wordlist file not found: {wordlist_file}")
        return

    output_path = os.path.abspath(output_path)
    subs_dir = os.path.join(output_path, "subs")
    subs_file = os.path.join(subs_dir, "puredns.subs.txt")
    all_subs_file = os.path.join(subs_dir, "all.subs.txt")
    
    os.makedirs(subs_dir, exist_ok=True)
    
    first_run = not (os.path.exists(subs_file) and os.path.getsize(subs_file) > 0)

    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_subs, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_newly_discovered:
            
            new_subs_path = tmp_new_subs.name
            newly_discovered_path = tmp_newly_discovered.name

        with open(domains_file, 'r') as f:
            domains = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        found_subs = set()
        
        for domain in domains:
            logger.info(f"Bruteforcing subdomains via PureDNS for: {domain}")
            try:
                # Matches: puredns bruteforce <wordlist> <domain> -q
                cmd = ["puredns", "bruteforce", wordlist_file, domain, "-q"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                
                if result.stdout:
                    for line in result.stdout.splitlines():
                        clean_line = line.replace("*.", "").replace("*", "").strip()
                        if clean_line:
                            found_subs.add(clean_line)
            except Exception as e:
                logger.error(f"Error running puredns for {domain}: {e}")

        sorted_subs = sorted(list(found_subs))
        with open(new_subs_path, 'w') as f:
            f.write("\n".join(sorted_subs) + ("\n" if sorted_subs else ""))

        newly_discovered = []
        if os.path.exists(all_subs_file):
            with open(all_subs_file, 'r') as f:
                existing_subs = set(line.strip() for line in f if line.strip())
            newly_discovered = [s for s in sorted_subs if s not in existing_subs]
        else:
            newly_discovered = sorted_subs

        if newly_discovered:
            with open(newly_discovered_path, 'w') as f:
                f.write("\n".join(newly_discovered) + "\n")
            
            logger.info(f"Discovered {len(newly_discovered)} new subdomains via PureDNS.")

            if notify_enabled and not first_run:
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New Subdomains (PureDNS)\n\n" + "\n".join(newly_discovered)
                    try:
                        subprocess.run(
                            ["notify", "-bulk", "-provider", "telegram"],
                            input=notify_msg,
                            text=True,
                            capture_output=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")

            if shutil.which("anew"):
                with open(newly_discovered_path, 'r') as f:
                    subprocess.run(["anew", all_subs_file], stdin=f)
            else:
                with open(all_subs_file, 'a') as f:
                    f.write("\n".join(newly_discovered) + "\n")

        shutil.copy(new_subs_path, subs_file)

    finally:
        if os.path.exists(new_subs_path):
            os.remove(new_subs_path)
        if os.path.exists(newly_discovered_path):
            os.remove(newly_discovered_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python puredns_enum.py <domains_file> <output_path> <wordlist_file> [notify_enabled]")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]
    wl_arg = sys.argv[3]
    notify_arg = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False

    puredns_enum(file_arg, out_arg, notify_arg, wl_arg)