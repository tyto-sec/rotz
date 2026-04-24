import os
import subprocess
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def aquatone_screenshots(subs_file, output_path):
    # Check whether the subdomains file exists
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    base_output = os.path.abspath(output_path)
    screenshots_dir = os.path.join(base_output, "screenshots", "aquatone")
    
    # Ensure the directory exists
    os.makedirs(screenshots_dir, exist_ok=True)

    logger.info(f"Starting Aquatone screenshots for: {subs_file}")
    
    try:
        # Aquatone reads from stdin
        # cmd: aquatone -out <dir> -scan-timeout <ms> -http-timeout <ms> -threads <int>
        cmd = [
            "aquatone",
            "-out", screenshots_dir,
            "-scan-timeout", "5000",
            "-http-timeout", "5000",
            "-threads", "200"
        ]
        
        # Read subdomains from file
        with open(subs_file, 'r') as f:
            # We use subprocess.run with stdin=f to mimic 'cat file | aquatone'
            # check=False mimics the '|| true' logic to keep the workflow moving
            result = subprocess.run(cmd, stdin=f, capture_output=False, text=True, check=False)
            
            if result.returncode != 0:
                logger.warning(f"Aquatone finished with exit code {result.returncode}, but continuing workflow...")
            else:
                logger.info(f"Aquatone scan completed. Results saved in: {screenshots_dir}")

    except Exception as e:
        logger.error(f"Error during aquatone execution: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 aquatone_screenshots.py '{{LIVE_SUBDOOMAINS_FILE}}' '{{CONTENT_OUTPUT_PATH}}'
    if len(sys.argv) < 3:
        print("Usage: python3 aquatone_screenshots.py <subs_file> <output_path>")
        sys.exit(1)

    file_input = sys.argv[1]
    path_output = sys.argv[2]

    aquatone_screenshots(file_input, path_output)
    # Force exit 0 to ensure the orchestrator (YAML/Rayder) doesn't stop on non-critical errors
    sys.exit(0)