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

def gowitness_screenshots(subs_file, output_path):
    # Check whether the subdomains file exists
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    screenshots_dir = os.path.join(os.path.abspath(output_path), "screenshots")
    
    # Ensure the screenshots directory exists
    os.makedirs(screenshots_dir, exist_ok=True)

    logger.info(f"Capturing screenshots via gowitness for: {subs_file}")
    
    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        cmd = [
            "gowitness", "scan", "file",
            "-f", subs_file,
            "--screenshot-path", screenshots_dir,
            "--screenshot-fullpage",
            "--chrome-user-agent", user_agent,
            "--chrome-header", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "--chrome-header", "Accept-Language: en-US,en;q=0.5",
            "--delay", "5", 
            "--timeout", "60",
            "--write-none"
        ]
        
        # Run gowitness
        result = subprocess.run(cmd, capture_output=False, text=True, check=False)
        
        if result.returncode == 0:
            logger.info(f"Gowitness scan completed. Screenshots saved in: {screenshots_dir}")
        else:
            logger.error(f"Gowitness finished with exit code {result.returncode}")

    except Exception as e:
        logger.error(f"Error executing gowitness: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 gowitness_screenshots.py <subs_file> <output_path>")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]

    gowitness_screenshots(file_arg, out_arg)