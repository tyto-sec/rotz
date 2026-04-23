import os
import subprocess
import shutil
import tempfile
import logging
import ipaddress
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def asn_discovery(organization, output_path, notify_enabled=False):
    if not organization:
        logger.error("Organization name is required.")
        return

    # Ensure output_path is absolute. 
    ips_dir = os.path.abspath(output_path)
    asn_ips_file = os.path.join(ips_dir, "asn.ips.txt")
    all_ips_file = os.path.join(ips_dir, "all.ips.txt")
    
    os.makedirs(ips_dir, exist_ok=True)
    
    first_run = not (os.path.exists(asn_ips_file) and os.path.getsize(asn_ips_file) > 0)

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_ips, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_newly_discovered:
            
            new_ips_path = tmp_new_ips.name
            newly_discovered_path = tmp_newly_discovered.name

        found_ips = set()
        
        # 1. Run metabigor to find network ranges
        logger.info(f"Discovering ASN IPs for organization: {organization}")
        try:
            # metabigor net --org -v
            cmd = ["metabigor", "net", "--org", "-v"]
            result = subprocess.run(cmd, input=organization, capture_output=True, text=True, check=False)
            
            # 2. Process output
            for line in result.stdout.splitlines():
                parts = line.split()
                # Metabigor -v usually outputs: "ASN | Org Name | CIDR" 
                # We look for the part that contains a '/' or looks like an IP
                for part in parts:
                    if '.' in part and (part[0].isdigit()):
                        try:
                            # Expansion logic
                            network = ipaddress.ip_network(part.strip(), strict=False)
                            if network.version == 4:
                                for ip in network:
                                    found_ips.add(str(ip))
                        except ValueError:
                            continue

        except Exception as e:
            logger.error(f"Error running metabigor: {e}")

        # Save unique results
        sorted_ips = sorted(list(found_ips))
        with open(new_ips_path, 'w') as f:
            f.write("\n".join(sorted_ips) + ("\n" if sorted_ips else ""))

        # 3. Compare with historical data
        newly_discovered = []
        if os.path.exists(all_ips_file):
            with open(all_ips_file, 'r') as f:
                existing_ips = set(line.strip() for line in f if line.strip())
            newly_discovered = [ip for ip in sorted_ips if ip not in existing_ips]
        else:
            newly_discovered = sorted_ips

        # 4. Process new discoveries
        if newly_discovered:
            with open(newly_discovered_path, 'w') as f:
                f.write("\n".join(newly_discovered) + "\n")
            
            logger.info(f"Discovered {len(newly_discovered)} new IPs via ASN lookup.")

            # Notification (Telegram via 'notify')
            if notify_enabled and not first_run:
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New ASN IPs\n\n" + "\n".join(newly_discovered)
                    try:
                        subprocess.run(
                            ["notify", "-bulk", "-provider", "telegram"],
                            input=notify_msg,
                            text=True,
                            capture_output=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")

            # Update the master file using 'anew' or Python
            if shutil.which("anew"):
                with open(newly_discovered_path, 'r') as f:
                    subprocess.run(["anew", all_ips_file], stdin=f)
            else:
                with open(all_ips_file, 'a') as f:
                    f.write("\n".join(newly_discovered) + "\n")

        # Update the latest-run cache
        shutil.copy(new_ips_path, asn_ips_file)

    finally:
        # Clean up temporary files
        if os.path.exists(new_ips_path):
            os.remove(new_ips_path)
        if os.path.exists(newly_discovered_path):
            os.remove(newly_discovered_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python asn_discovery.py <organization> <ips_output_path> [notify_enabled]")
        sys.exit(1)

    org_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    asn_discovery(org_arg, out_arg, notify_arg)