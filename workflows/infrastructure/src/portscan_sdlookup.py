import os
import subprocess
import shutil
import json
import logging
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def portscan_sdlookup(ips_file, output_path, notify_enabled=False):
    # Check whether the IPs file exists
    if not os.path.isfile(ips_file):
        logger.error(f"IPs file not found: {ips_file}")
        return

    # Ensure output_path is absolute and points to the scans directory
    # Based on the bash script logic: output_path/ips/scans
    scans_dir = os.path.join(os.path.abspath(output_path), "scans")
    os.makedirs(scans_dir, exist_ok=True)

    # Read IPs from file (ignoring comments and empty lines)
    with open(ips_file, 'r') as f:
        ips_list = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    if not ips_list:
        logger.warning(f"No IPs found in {ips_file} to scan.")
        return

    for ip in ips_list:
        logger.info(f"Scanning IP via SDLookup: {ip}")
        scan_file = os.path.join(scans_dir, f"{ip}.scan.json")
        
        try:
            # 1. Run sdlookup -json for the IP
            # cmd: sdlookup -json
            cmd = ["sdlookup", "-json"]
            result = subprocess.run(cmd, input=ip, capture_output=True, text=True, check=False)

            if not result.stdout.strip():
                logger.warning(f"No data returned for {ip}")
                continue

            # 2. Save the JSON output
            try:
                data = json.loads(result.stdout)
                with open(scan_file, 'w', encoding='utf-8') as sf:
                    json.dump(data, sf, indent=4)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON output for {ip}")
                continue

            # 3. Check for interesting findings (Vulns or unusual ports)
            vulns = data.get('vulns') or []
            ports = data.get('ports') or []
            
            # Filter unusual ports (not 80 or 443)
            # Assuming ports is a list of integers based on the original logic
            unusual_ports = [p for p in ports if p not in (80, 443)]

            # 4. Notify if findings exist
            if notify_enabled and (len(vulns) > 0 or len(unusual_ports) > 0):
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Preparing the notification message
                    findings_summary = f"[{timestamp}] SDLookup findings for {ip}\n\n"
                    findings_summary += json.dumps(data, indent=2)
                    
                    try:
                        subprocess.run(
                            ["notify", "-bulk", "-provider", "telegram"],
                            input=findings_summary,
                            text=True,
                            capture_output=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification for {ip}: {e}")

        except Exception as e:
            logger.error(f"Error processing IP {ip}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python portscan_sdlookup.py <ips_file> <output_path> [notify_enabled]")
        sys.exit(1)

    ips_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    portscan_sdlookup(ips_arg, out_arg, notify_arg)