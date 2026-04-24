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

def arjun_enum(input_file, output_path):
    # Check whether the input file exists (URLs with parameters)
    if not os.path.isfile(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    # Directory setup based on YAML: CONTENT_OUTPUT_PATH
    base_output = os.path.abspath(output_path)
    urls_dir = os.path.join(base_output, "urls")
    arjun_dir = os.path.join(urls_dir, "arjun")
    arjun_output_file = os.path.join(urls_dir, "all.arjun.urls.txt")
    all_urls_file = os.path.join(urls_dir, "all.urls.txt")
    
    os.makedirs(arjun_dir, exist_ok=True)

    logger.info(f"Starting Arjun parameter discovery for: {input_file}")
    
    try:
        # Check if arjun is installed
        if not shutil.which("arjun"):
            logger.error("Arjun is not installed or not in PATH. Please install it with 'pip install arjun'.")
            return
            
        # 1. Run Arjun
        # -i: input file
        # -oT: output in Text format
        # -t / -d: threads and delay for stability
        # --rate-limit: requests per second
        # --stable: better detection for dynamic pages
        cmd = [
            "arjun", 
            "-i", input_file, 
            "-oT", arjun_output_file, 
            "-t", "2", 
            "-d", "1", 
            "--rate-limit", "20", 
            "--stable"
        ]
        
        # Arjun outputs findings to the file specified in -oT
        result = subprocess.run(cmd, capture_output=False, text=True, check=False)
        
        if result.returncode != 0:
            logger.warning(f"Arjun finished with exit code {result.returncode}. Investigation of output recommended.")

        # 2. Update master URLs file with findings
        if os.path.exists(arjun_output_file) and os.path.getsize(arjun_output_file) > 0:
            logger.info(f"Updating master URL list with Arjun findings: {all_urls_file}")
            
            if shutil.which("anew"):
                with open(arjun_output_file, 'r') as f:
                    subprocess.run(["anew", all_urls_file], stdin=f)
            else:
                # Python fallback for anew
                with open(arjun_output_file, 'r') as f:
                    new_urls = set(l.strip() for l in f if l.strip())
                
                existing = set()
                if os.path.exists(all_urls_file):
                    with open(all_urls_file, 'r') as f:
                        existing = set(l.strip() for l in f if l.strip())
                
                truly_new = [url for url in new_urls if url not in existing]
                if truly_new:
                    with open(all_urls_file, 'a') as f:
                        f.write("\n".join(truly_new) + "\n")
        else:
            logger.info("Arjun did not discover any additional parameters/URLs.")

    except Exception as e:
        logger.error(f"Error executing Arjun: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 arjun_enum.py "{{PARAMS_URLS_FILE}}" "{{CONTENT_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 arjun_enum.py <input_file> <output_path>")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]

    arjun_enum(file_arg, out_arg)