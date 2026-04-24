import os
import subprocess
import shutil
import logging
from urllib.parse import urlparse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def download_js_files(urls_file, output_path):
    """
    Downloads JS files from a list of URLs and beautifies them.
    urls_file: Path to the file containing JS URLs
    output_path: The directory where JS files will be saved (JS_DOWNLOAD_FOLDER)
    """
    
    if not os.path.isfile(urls_file):
        logger.error(f"URLs file not found: {urls_file}")
        return

    # Directory setup
    # output_path corresponds to JS_DOWNLOAD_FOLDER
    base_dir = os.path.abspath(output_path)
    downloads_dir = os.path.join(base_dir, "js_files")
    beautified_dir = os.path.join(base_dir, "beautified")

    os.makedirs(downloads_dir, exist_ok=True)
    os.makedirs(beautified_dir, exist_ok=True)

    # 1. Download JS Files
    logger.info(f"Downloading JavaScript files from: {urls_file}")
    
    with open(urls_file, 'r', encoding='utf-8', errors='ignore') as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    for url in urls:
        # Resolve clean filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Fallback for URLs without a proper filename in path
        if not filename or not filename.endswith('.js'):
            # Create a filename from hostname and hash/query if necessary
            filename = f"{parsed_url.netloc}_{hash(url)}.js"
        
        target_file = os.path.join(downloads_dir, filename)
        
        logger.info(f"Downloading: {url}")
        try:
            # Using wget via subprocess to mimic bash logic (-q for quiet, -O for specific path)
            subprocess.run(["wget", "-q", "-O", target_file, url], check=False)
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")

    # 2. Beautify JS Files
    if shutil.which("js-beautify"):
        logger.info("Beautifying downloaded JavaScript files...")
        for js_file in os.listdir(downloads_dir):
            if js_file.endswith(".js"):
                src_path = os.path.join(downloads_dir, js_file)
                dst_path = os.path.join(beautified_dir, js_file)
                
                try:
                    # js-beautify < input > output
                    with open(src_path, 'r') as f_in, open(dst_path, 'w') as f_out:
                        subprocess.run(["js-beautify"], stdin=f_in, stdout=f_out, check=False)
                except Exception as e:
                    logger.warning(f"Could not beautify {js_file}: {e}")
    else:
        logger.warning("js-beautify not found in PATH. Skipping beautification.")

if __name__ == "__main__":
    import sys
    # Usage based on YAML vars: 
    # python3 download_js_files.py "{{SELECTED_JS_FILES}}" "{{JS_DOWNLOAD_FOLDER}}"
    if len(sys.argv) < 3:
        print("Usage: python3 download_js_files.py <urls_file> <output_path>")
        sys.exit(1)

    urls_arg = sys.argv[1]
    out_arg = sys.argv[2]

    download_js_files(urls_arg, out_arg)