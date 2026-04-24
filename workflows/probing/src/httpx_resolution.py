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

def httpx_resolution(subs_file, output_path, notify_enabled=False):
    # Check whether the subdomains file exists
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    # Ensure output_path is absolute. 
    live_dir = os.path.abspath(output_path)
    all_live_file = os.path.join(live_dir, "all.live.subs.txt")
    
    os.makedirs(live_dir, exist_ok=True)
    
    # Check if this is the first run to avoid notification spam
    first_run = not (os.path.exists(all_live_file) and os.path.getsize(all_live_file) > 0)

    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_httpx, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_new_live:
            
            httpx_output_path = tmp_httpx.name
            new_live_path = tmp_new_live.name

        # 1. Run httpx to resolve live hosts
        logger.info(f"Probing live subdomains via httpx from: {subs_file}")
        try:
            # httpx -silent -threads 200 -timeout 5 -retries 0
            # We pass the input file using -l flag for better stability
            cmd = [
                "httpx", 
                "-l", subs_file,
                "-silent", 
                "-threads", "200", 
                "-timeout", "5", 
                "-retries", "0",
                "-o", httpx_output_path
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=False)
        except Exception as e:
            logger.error(f"Error running httpx: {e}")
            return

        # 2. Extract unique live hosts found in this round
        current_live = set()
        if os.path.exists(httpx_output_path):
            with open(httpx_output_path, 'r') as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line:
                        current_live.add(clean_line)

        if not current_live:
            logger.info("No live subdomains identified.")
            return

        # 3. Compare with historical data to find NEW live subdomains
        existing_live = set()
        if os.path.exists(all_live_file):
            with open(all_live_file, 'r') as f:
                existing_live = set(line.strip() for line in f if line.strip())
        
        newly_discovered = [host for host in sorted(list(current_live)) if host not in existing_live]

        # 4. Process new discoveries
        if newly_discovered:
            with open(new_live_path, 'w') as f:
                f.write("\n".join(newly_discovered) + "\n")
            
            logger.info(f"Discovered {len(newly_discovered)} new live subdomains.")

            # Notification (Telegram via 'notify')
            if notify_enabled and not first_run:
                notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                if shutil.which("notify") and os.path.isfile(notify_config_path):
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notify_msg = f"[{timestamp}] New Live Subdomains (httpx)\n\n" + "\n".join(newly_discovered)
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
                with open(new_live_path, 'r') as f:
                    subprocess.run(["anew", all_live_file], stdin=f)
            else:
                with open(all_live_file, 'a') as f:
                    f.write("\n".join(newly_discovered) + "\n")

    finally:
        # Cleanup temporary files
        if os.path.exists(httpx_output_path):
            os.remove(httpx_output_path)
        if os.path.exists(new_live_path):
            os.remove(new_live_path)

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 httpx_resolution.py <subs_file> <output_path> [notify_enabled]
    if len(sys.argv) < 3:
        print("Usage: python3 httpx_resolution.py <subs_file> <output_path> [notify_enabled]")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    httpx_resolution(file_arg, out_arg, notify_arg)