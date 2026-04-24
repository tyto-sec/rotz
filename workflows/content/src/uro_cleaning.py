import os
import subprocess
import shutil
import tempfile
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def uro_cleaning(urls_file, output_path):
    # Check whether the input URLs file exists
    if not os.path.isfile(urls_file):
        logger.error(f"Input URLs file not found: {urls_file}")
        return

    base_output = os.path.abspath(output_path)
    urls_dir = os.path.join(base_output, "urls")
    cleaned_urls_file = os.path.join(urls_dir, "all.cleaned.urls.txt")
    
    os.makedirs(urls_dir, exist_ok=True)

    logger.info(f"Cleaning and deduplicating URLs via uro: {urls_file}")
    
    try:
        # Create a temporary file for the current uro output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_cleaned:
            tmp_cleaned_path = tmp_cleaned.name

        # 1. Run uro
        # cmd: cat urls_file | uro
        with open(urls_file, 'r', encoding='utf-8', errors='ignore') as f_in:
            cmd = ["uro"]
            # Check if uro is installed
            if not shutil.which("uro"):
                logger.error("uro is not installed or not in PATH. Please install it with 'pip install uro'.")
                return
            
            # Execute uro and write to temp file
            with open(tmp_cleaned_path, 'w') as f_out:
                subprocess.run(cmd, stdin=f_in, stdout=f_out, stderr=subprocess.PIPE, text=True, check=False)

        # 2. Process cleaned results
        if os.path.exists(tmp_cleaned_path) and os.path.getsize(tmp_cleaned_path) > 0:
            logger.info("Updating cleaned URLs file...")
            
            # We use anew logic to maintain uniqueness in the master cleaned file
            if shutil.which("anew"):
                with open(tmp_cleaned_path, 'r') as f:
                    subprocess.run(["anew", cleaned_urls_file], stdin=f)
            else:
                # Python fallback for anew
                with open(tmp_cleaned_path, 'r') as f:
                    new_urls = set(l.strip() for l in f if l.strip())
                
                existing = set()
                if os.path.exists(cleaned_urls_file):
                    with open(cleaned_urls_file, 'r') as f:
                        existing = set(l.strip() for l in f if l.strip())
                
                truly_new = [url for url in new_urls if url not in existing]
                if truly_new:
                    with open(cleaned_urls_file, 'a') as f:
                        f.write("\n".join(truly_new) + "\n")
            
            logger.info(f"Cleaning finished. Results saved/updated in: {cleaned_urls_file}")
        else:
            logger.info("uro returned no results (input might have been empty or invalid).")

    except Exception as e:
        logger.error(f"Error executing uro: {e}")

    finally:
        # Cleanup temp file
        if 'tmp_cleaned_path' in locals() and os.path.exists(tmp_cleaned_path):
            os.remove(tmp_cleaned_path)

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 uro_cleaning.py "{{ALL_URLS_FILE}}" "{{CONTENT_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 uro_cleaning.py <urls_file> <output_path>")
        sys.exit(1)

    file_input = sys.argv[1]
    path_output = sys.argv[2]

    uro_cleaning(file_input, path_output)