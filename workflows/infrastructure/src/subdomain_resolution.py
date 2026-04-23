import os
import subprocess
import shutil
import tempfile
import logging
import re
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def subdomain_resolution(subdomains_path, output_path, notify_enabled=False):
    if os.path.isdir(subdomains_path):
        subdomains_file = os.path.join(subdomains_path, "all.subs.txt")
    else:
        subdomains_file = subdomains_path

    if not os.path.isfile(subdomains_file):
        logger.error(f"Subdomains file not found: {subdomains_file}")
        return

    # Ensure output_path (IPS_OUTPUT_PATH) is absolute
    ips_dir = os.path.abspath(output_path)
    resolved_ips_file = os.path.join(ips_dir, "subdomains.resolved.ips.txt")
    all_ips_file = os.path.join(ips_dir, "all.ips.txt")
    
    os.makedirs(ips_dir, exist_ok=True)
    
    first_run = not (os.path.exists(resolved_ips_file) and os.path.getsize(resolved_ips_file) > 0)

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_ips, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_discovered:
            
            new_ips_path = tmp_new_ips.name
            newly_discovered_path = tmp_new_discovered.name

        found_ips = set()

        # 1. Read subdomains (ignoring comments and empty lines)
        with open(subdomains_file, 'r') as f:
            subdomains = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

        if not subdomains:
            logger.warning(f"No subdomains found in {subdomains_file} to resolve.")
            return

        # 2. Run httpx to resolve IPs
        logger.info(f"Resolving {len(subdomains)} subdomains via httpx...")
        try:
            input_data = "\n".join(subdomains)
            # httpx -ip -silent
            cmd = ["httpx", "-ip", "-silent"]
            result = subprocess.run(cmd, input=input_data, capture_output=True, text=True, check=False)
            
            # 3. Parse IPs from httpx output (format typically: http://target [IP])
            # Regex to find content inside brackets
            ip_pattern = re.compile(r'\[([^\]]+)\]')
            
            for line in result.stdout.splitlines():
                match = ip_pattern.search(line)
                if match:
                    # Some httpx versions might put multiple IPs or CDNs here
                    ip = match.group(1)
                    if ip:
                        found_ips.add(ip)

        except Exception as e:
            logger.error(f"Error running httpx: {e}")

        # Save unique results
        sorted_ips = sorted(list(found_ips))
        with open(new_ips_path, 'w') as f:
            f.write("\n".join(sorted_ips) + ("\n" if sorted_ips else ""))

        # 4. Compare with historical data
        newly_discovered = []
        if os.path.exists(all_ips_file):
            with open(all_ips_file, 'r') as f:
                existing_ips = set(line.strip() for line in f if line.strip())
            newly_discovered = [ip for ip in sorted_ips if ip not in existing_ips]
        else:
            newly_discovered = sorted_ips

        # 5. Process new discoveries
        if newly_discovered:
            with open(newly_discovered_path, 'w') as f:
                f.write("\n".join(newly_discovered) + "\n")
            
            logger.info(f"Discovered {len(newly_discovered)} new IPs from subdomain resolution.")

            # Notification (Telegram via 'notify')
            if notify_enabled and not first_run:
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New Subdomain IPs\n\n" + "\n".join(newly_discovered)
                    try:
                        subprocess.run(
                            ["notify", "-bulk", "-provider", "telegram"],
                            input=notify_msg,
                            text=True,
                            capture_output=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")

            # Update files using 'anew' or Python
            if shutil.which("anew"):
                with open(newly_discovered_path, 'r') as f:
                    subprocess.run(["anew", all_ips_file], stdin=f)
                with open(newly_discovered_path, 'r') as f:
                    subprocess.run(["anew", resolved_ips_file], stdin=f)
            else:
                with open(all_ips_file, 'a') as f:
                    f.write("\n".join(newly_discovered) + "\n")
                with open(resolved_ips_file, 'a') as f:
                    f.write("\n".join(newly_discovered) + "\n")

    finally:
        if os.path.exists(new_ips_path):
            os.remove(new_ips_path)
        if os.path.exists(newly_discovered_path):
            os.remove(newly_discovered_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python subdomain_resolution.py <subdomains_path> <ips_output_path> [notify_enabled]")
        sys.exit(1)

    subs_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    subdomain_resolution(subs_arg, out_arg, notify_arg)