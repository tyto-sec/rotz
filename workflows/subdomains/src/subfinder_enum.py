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

def subfinder_enum(domains_file, output_path, notify_enabled=False):
    # Check whether the domains file exists
    if not os.path.isfile(domains_file):
        logger.error(f"Domains file not found: {domains_file}")
        return

    subs_dir = os.path.join(output_path, "subs")
    subs_file = os.path.join(subs_dir, "subfinder.subs.txt")
    all_subs_file = os.path.join(subs_dir, "all.subs.txt")
    
    os.makedirs(subs_dir, exist_ok=True)
    
    first_run = not (os.path.exists(subs_file) and os.path.getsize(subs_file) > 0)

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_subs, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_newly_discovered:
            
            new_subs_path = tmp_new_subs.name
            newly_discovered_path = tmp_newly_discovered.name

        # 1. Read domains (ignoring comments and empty lines)
        with open(domains_file, 'r') as f:
            domains = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        found_subs = set()
        
        # 2. Run Subfinder for each domain
        for domain in domains:
            logger.info(f"Enumerating subdomains for: {domain}")
            try:
                cmd = ["subfinder", "-d", domain, "-silent", "-recursive", "-all"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                for line in result.stdout.splitlines():
                    clean_line = line.replace("*.", "").replace("*", "").strip()
                    if clean_line:
                        found_subs.add(clean_line)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error running subfinder for {domain}: {e}")

        # Save unique results found in this round
        sorted_subs = sorted(list(found_subs))
        with open(new_subs_path, 'w') as f:
            f.write("\n".join(sorted_subs) + "\n")

        # 3. Compare with historical data (all.subs.txt)
        newly_discovered = []
        if os.path.exists(all_subs_file):
            with open(all_subs_file, 'r') as f:
                existing_subs = set(line.strip() for line in f if line.strip())
            newly_discovered = [s for s in sorted_subs if s not in existing_subs]
        else:
            newly_discovered = sorted_subs

        # 4. Process new discoveries
        if newly_discovered:
            with open(newly_discovered_path, 'w') as f:
                f.write("\n".join(newly_discovered) + "\n")
            
            logger.info(f"Discovered {len(newly_discovered)} new subdomains.")

            # Notification (Telegram via 'notify')
            if notify_enabled and not first_run:
                if shutil.which("notify"):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New Subdomains (Subfinder)\n\n" + "\n".join(newly_discovered)
                    try:
                        subprocess.run(
                            ["notify", "-bulk", "-provider", "telegram"],
                            input=notify_msg,
                            text=True,
                            capture_output=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")

            # Update the master file using 'anew' or Python logic
            if shutil.which("anew"):
                with open(newly_discovered_path, 'r') as f:
                    subprocess.run(["anew", all_subs_file], stdin=f)
            else:
                # Fallback if 'anew' is not installed
                with open(all_subs_file, 'a') as f:
                    f.write("\n".join(newly_discovered) + "\n")

        # Update the latest-run cache
        shutil.copy(new_subs_path, subs_file)

    finally:
        # Clean up temporary files
        if 'new_subs_path' in locals() and os.path.exists(new_subs_path):
            os.remove(new_subs_path)
        if 'newly_discovered_path' in locals() and os.path.exists(newly_discovered_path):
            os.remove(newly_discovered_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python subfinder_enum.py <domains_file> <output_path> [notify_enabled(true/false)]")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    subfinder_enum(file_arg, out_arg, notify_arg)