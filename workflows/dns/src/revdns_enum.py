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

def revdns_enum(ips_file, output_path, notify_enabled=False, domains_file=None):
    # Mandatory Domain File Check
    if not domains_file or not os.path.isfile(domains_file):
        logger.error(f"Mandatory domains file not found or not provided: {domains_file}")
        return

    # Check if IPs file exists
    if not os.path.isfile(ips_file):
        logger.error(f"IPs file not found: {ips_file}")
        return

    # Directory setup
    dns_dir = os.path.abspath(output_path)
    # Replicating the project structure: output/tesla/dns -> output/tesla/subs
    subs_dir = os.path.join(os.path.dirname(dns_dir), "subs")
    all_subs_file = os.path.join(subs_dir, "all.subs.txt")
    
    revdns_lookup_file = os.path.join(dns_dir, "revdns.ip.lookup.txt")
    revdns_domains_file = os.path.join(subs_dir, "revdns.domains.txt")
    
    os.makedirs(dns_dir, exist_ok=True)
    os.makedirs(subs_dir, exist_ok=True)

    first_run = not (os.path.exists(revdns_domains_file) and os.path.getsize(revdns_domains_file) > 0)

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_domains, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_newly_discovered, \
             tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_filtered:
            
            new_domains_path = tmp_new_domains.name
            newly_discovered_path = tmp_newly_discovered.name
            filtered_path = tmp_filtered.name

        # 1. Run hakrevdns
        logger.info(f"Performing Reverse DNS lookup for IPs in: {ips_file}")
        found_mappings = []
        try:
            with open(ips_file, 'r') as f:
                cmd = ["hakrevdns", "-r", "1.1.1.1"]
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, check=False)
                
                if result.stdout:
                    found_mappings = result.stdout.splitlines()
                    # Append mappings to lookup file
                    if shutil.which("anew"):
                        subprocess.run(["anew", revdns_lookup_file], input=result.stdout, text=True)
                    else:
                        with open(revdns_lookup_file, 'a') as alf:
                            alf.write(result.stdout)
        except Exception as e:
            logger.error(f"Error running hakrevdns: {e}")
            return

        # 2. Extract unique domains from output (format: <IP> <DOMAIN>)
        current_domains = set()
        for line in found_mappings:
            parts = line.split()
            if len(parts) >= 2:
                domain = parts[1].strip().rstrip('.').lower()
                if domain:
                    current_domains.add(domain)

        if not current_domains:
            logger.info("No domains found via Reverse DNS.")
            return

        # 3. Compare with historical data
        existing_rev_domains = set()
        if os.path.exists(revdns_domains_file):
            with open(revdns_domains_file, 'r') as f:
                existing_rev_domains = set(l.strip() for l in f if l.strip())
        
        newly_discovered = [d for d in current_domains if d not in existing_rev_domains]

        if newly_discovered:
            # 4. Mandatory Filter based on target domains list (e.g., tesla.com)
            filtered_newly = []
            with open(domains_file, 'r') as f:
                keywords = [l.strip().lower() for l in f if l.strip() and not l.strip().startswith('#')]
            
            for domain in newly_discovered:
                if any(kw in domain for kw in keywords):
                    filtered_newly.append(domain)

            # 5. Process filtered results
            if filtered_newly:
                logger.info(f"Discovered {len(filtered_newly)} new relevant domains via Reverse DNS.")
                
                # Notification
                if notify_enabled and not first_run:
                    notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                    if shutil.which("notify") and os.path.isfile(notify_config_path):
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        notify_msg = f"[{timestamp}] New Subdomains (Reverse DNS)\n\n" + "\n".join(filtered_newly)
                        try:
                            subprocess.run(
                                ["notify", "-bulk", "-provider", "telegram"],
                                input=notify_msg,
                                text=True,
                                capture_output=True
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send notification: {e}")

                # Update master files
                if shutil.which("anew"):
                    subprocess.run(["anew", revdns_domains_file], input="\n".join(newly_discovered), text=True)
                    subprocess.run(["anew", all_subs_file], input="\n".join(filtered_newly), text=True)
                else:
                    with open(revdns_domains_file, 'a') as f:
                        f.write("\n".join(newly_discovered) + "\n")
                    with open(all_subs_file, 'a') as f:
                        f.write("\n".join(filtered_newly) + "\n")

    finally:
        # Cleanup
        for p in [new_domains_path, newly_discovered_path, filtered_path]:
            if os.path.exists(p):
                os.remove(p)

if __name__ == "__main__":
    import sys
    # Usage based on Yaml: python revdns_enum.py <ips_file> <dns_output_path> <notify_enabled> <domains_file>
    if len(sys.argv) < 5:
        print("Usage: python revdns_enum.py <ips_file> <dns_output_path> <notify_enabled> <domains_file>")
        sys.exit(1)

    ips_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true"
    dom_arg = sys.argv[4]

    revdns_enum(ips_arg, out_arg, notify_arg, dom_arg)