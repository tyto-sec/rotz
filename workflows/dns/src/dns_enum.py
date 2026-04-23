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

def dns_enum(subs_file, output_path, notify_enabled=False):
    # Check whether the subdomains file exists
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    # Ensure output_path (DNS_OUTPUT_PATH) is absolute
    dns_dir = os.path.abspath(output_path)
    all_dns_file = os.path.join(dns_dir, "all.dns.txt")
    txt_records_file = os.path.join(dns_dir, "txt_records.dns.txt")
    cname_file = os.path.join(dns_dir, "cname_records.dns.txt")
    vuln_file = os.path.join(dns_dir, "vulnerable.email_spoofing.dns.txt")
    
    os.makedirs(dns_dir, exist_ok=True)

    try:
        # Create temporary file for new findings
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_vulns:
            new_vulns_path = tmp_new_vulns.name

        # 1. Run dnsx -recon to gather DNS records
        logger.info(f"Gathering DNS records via dnsx for: {subs_file}")
        try:
            # dnsx -silent -recon -nc -o output -l input
            cmd = ["dnsx", "-silent", "-recon", "-nc", "-l", subs_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.stdout:
                with open(all_dns_file, 'w') as f:
                    f.write(result.stdout)
            else:
                logger.info("No DNS records found.")
                return
        except Exception as e:
            logger.error(f"Error running dnsx: {e}")
            return

        # 2. Extract TXT and CNAME records (mimics grep logic)
        txt_records = []
        cname_records = []
        
        for line in result.stdout.splitlines():
            # Use 'anew' logic or simple set for TXT
            if ' TXT ' in line:
                txt_records.append(line)
            # Use 'anew' logic or simple set for CNAME
            if ' CNAME ' in line:
                cname_records.append(line)

        # Update TXT and CNAME files
        for record_list, target_file in [(txt_records, txt_records_file), (cname_records, cname_file)]:
            if record_list and shutil.which("anew"):
                process = subprocess.Popen(["anew", target_file], stdin=subprocess.PIPE, text=True)
                process.communicate(input="\n".join(record_list))
            elif record_list:
                with open(target_file, 'a') as f:
                    f.write("\n".join(record_list) + "\n")

        # 3. Identify potential Email Spoofing (SPF vulnerabilities)
        # Logic: grep TXT records for v=spf1 and softened 'all' (~all or ?all)
        new_vulns = []
        if txt_records:
            for record in txt_records:
                # Case insensitive check for SPF and softfail/neutral
                rec_lower = record.lower()
                if 'v=spf1' in rec_lower and ('~all' in rec_lower or '?all' in rec_lower):
                    new_vulns.append(record)

        if new_vulns:
            # Check what's actually NEW for the vuln_file
            if shutil.which("anew"):
                # Use anew to get only the unique new lines into our temp file
                # and simultaneously update the main vuln file
                process = subprocess.run(
                    ["anew", vuln_file], 
                    input="\n".join(new_vulns), 
                    capture_output=True, 
                    text=True
                )
                # anew stdout contains only the new lines added
                unique_new_vulns = process.stdout.strip()
            else:
                # Fallback: simple append (less accurate for "new" detection)
                unique_new_vulns = "\n".join(new_vulns)
                with open(vuln_file, 'a') as f:
                    f.write(unique_new_vulns + "\n")

            # 4. Handle Notifications
            if notify_enabled and unique_new_vulns:
                logger.info(f"Potential email spoofing identified on {len(unique_new_vulns.splitlines())} domains.")
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New potential email spoofing domains\n\n{unique_new_vulns}"
                    try:
                        subprocess.run(
                            ["notify", "-bulk", "-provider", "telegram"],
                            input=notify_msg,
                            text=True,
                            capture_output=True
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send notification: {e}")

    finally:
        # Cleanup
        if os.path.exists(new_vulns_path):
            os.remove(new_vulns_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 dns_enum.py <subs_file> <output_path> [notify_enabled]")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    dns_enum(file_arg, out_arg, notify_arg)