import os
import subprocess
import shutil
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def httpx_resolution(urls_file, output_path):
    # Check whether the input URLs file exists
    if not os.path.isfile(urls_file):
        logger.error(f"Input URLs file not found: {urls_file}")
        return

    # Directory setup based on YAML: CONTENT_OUTPUT_PATH
    # output_path is output/tesla/content
    base_output = os.path.abspath(output_path)
    urls_dir = os.path.join(base_output, "urls")
    live_urls_file = os.path.join(urls_dir, "all.live.urls.txt")
    
    os.makedirs(urls_dir, exist_ok=True)

    logger.info(f"Probing URLs for HTTP 200 via httpx: {urls_file}")
    
    try:
        # Use anew logic or simple update of the live_urls_file
        # cmd: httpx -silent -mc 200 -threads 100
        cmd = [
            "httpx",
            "-l", urls_file,
            "-silent",
            "-mc", "200",
            "-threads", "100"
        ]
        
        # We run httpx and capture its output
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.stdout:
            live_findings = result.stdout.strip()
            if live_findings:
                # Update the master live file using anew if available
                if shutil.which("anew"):
                    subprocess.run(["anew", live_urls_file], input=live_findings, text=True)
                else:
                    # Python fallback for anew logic
                    discovered = set(live_findings.splitlines())
                    existing = set()
                    if os.path.exists(live_urls_file):
                        with open(live_urls_file, 'r') as f:
                            existing = set(l.strip() for l in f if l.strip())
                    
                    truly_new = [url for url in discovered if url not in existing]
                    if truly_new:
                        with open(live_urls_file, 'a') as f:
                            f.write("\n".join(truly_new) + "\n")
                
                logger.info(f"Live resolution finished. Results appended to: {live_urls_file}")
        else:
            logger.info("No live URLs (HTTP 200) identified from the input.")

    except Exception as e:
        logger.error(f"Error executing httpx: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 httpx_resolution.py "{{GAU_URLS_FILE}}" "{{CONTENT_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 httpx_resolution.py <urls_file> <output_path>")
        sys.exit(1)

    file_input = sys.argv[1]
    path_output = sys.argv[2]

    httpx_resolution(file_input, path_output)