import os
import subprocess
import shutil
import logging
import tempfile
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def naabu_scan(input_file, output_path, notify_enabled=False):
    if not os.path.isfile(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    naabu_dir = os.path.join(os.path.abspath(output_path), "naabu")
    os.makedirs(naabu_dir, exist_ok=True)
    master_ports_file = os.path.join(naabu_dir, "open_ports.txt")
    
    first_run = not (os.path.exists(master_ports_file) and os.path.getsize(master_ports_file) > 0)

    try:
        # --- STRIP HIDDEN CHARACTERS ---
        sanitized_targets = []
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                # This regex-like strip removes \r, \n, and spaces
                clean = "".join(line.split()).lower() 
                if not clean or clean.startswith('#'):
                    continue
                # Remove common garbage
                clean = clean.replace("https://", "").replace("http://", "").split('/')[0].split(':')[0]
                if clean:
                    sanitized_targets.append(clean)

        if not sanitized_targets:
            logger.warning(f"No valid targets found in {input_file}")
            return

        # Create a clean temp file for Naabu to read
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
            tmp_file.write("\n".join(sanitized_targets) + "\n")
            sanitized_path = tmp_file.name

        logger.info(f"Starting Naabu scan on {len(sanitized_targets)} targets from: {input_file}")
        
        ports = "80,443,8080,8443,3000,4000,5000,88000,9000,5000,8888,8181"
        
        # Use simple CONNECT scan (-s c) if not running as root, 
        # and ensure -Pn is used to skip host discovery if ICMP is blocked
        cmd = [
            "naabu", 
            "-list", sanitized_path, 
            "-port", ports, 
            "-silent",
            "-rate", "1000",
            "-Pn",            # Skip host discovery
            "-scan-all-ips",  # Resolve hostnames to IPs and scan all
            "-ip-version", "4" # Force IPv4 to avoid resolution confusion
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        logger.debug(f"Naabu Command: {' '.join(cmd)}")
        logger.debug(f"Naabu Return Code: {result.returncode}")
        logger.debug(f"Naabu Stdout: {result.stdout.strip()}")

        # DEBUG: Let's see what's happening
        if result.stderr:
            logger.debug(f"Naabu Stderr: {result.stderr.strip()}")

        # Cleanup sanitized file
        if os.path.exists(sanitized_path):
            os.remove(sanitized_path)

        if not result.stdout.strip():
            logger.info("No open ports found.")
            return

        # --- PROCESS FINDINGS ---
        current_findings = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        
        existing_findings = set()
        if os.path.exists(master_ports_file):
            with open(master_ports_file, 'r') as f:
                existing_findings = set(line.strip() for line in f if line.strip())

        new_findings = [line for line in current_findings if line not in existing_findings]

        if new_findings:
            logger.info(f"Discovered {len(new_findings)} NEW open ports.")
            with open(master_ports_file, 'a') as f:
                f.write("\n".join(new_findings) + "\n")

            if notify_enabled and not first_run:
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New Open Ports\n\n" + "\n".join(new_findings)
                    subprocess.run(["notify", "-bulk", "-provider", "telegram"], input=notify_msg, text=True, capture_output=True)

    except Exception as e:
        logger.error(f"Error in naabu_scan: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 portscan_naabu.py <input_file> <output_path> [notify]")
        sys.exit(1)
    
    naabu_scan(sys.argv[1], sys.argv[2], sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False)