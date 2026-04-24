import os
import subprocess
import shutil
import logging
import glob

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def paramspider_enum(subs_file, output_path):
    # Check whether the subdomains file exists
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    base_output = os.path.abspath(output_path)
    urls_dir = os.path.join(base_output, "urls")
    paramspider_dir = os.path.join(urls_dir, "paramspider")
    all_paramspider_file = os.path.join(urls_dir, "all.paramspider.urls.txt")
    all_urls_file = os.path.join(urls_dir, "all.urls.txt")
    
    os.makedirs(paramspider_dir, exist_ok=True)

    logger.info(f"Starting ParamSpider for: {subs_file}")
    
    try:
        # 1. Run ParamSpider
        # ParamSpider creates a 'results' directory in the current working directory
        cmd = ["paramspider", "-l", subs_file, "-s"]
        subprocess.run(cmd, capture_output=False, text=True, check=False)

        # 2. Manage the results
        # Original logic: Move 'results/*' to paramspider_dir and delete 'results'
        if os.path.exists("results") and os.path.isdir("results"):
            logger.info("Moving results to output directory...")
            for item in os.listdir("results"):
                src = os.path.join("results", item)
                dst = os.path.join(paramspider_dir, item)
                # Shutil move handles files or directories
                shutil.move(src, dst)
            shutil.rmtree("results")

        # 3. Consolidate ParamSpider findings
        # Original: cat paramspider_dir/* | anew all_paramspider_file
        discovered_urls = []
        pattern = os.path.join(paramspider_dir, "*")
        for filepath in glob.glob(pattern):
            if os.path.isfile(filepath):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    discovered_urls.extend(f.read().splitlines())

        if discovered_urls:
            # deduplicate
            unique_param_urls = sorted(list(set(discovered_urls)))
            
            # Update all.paramspider.urls.txt
            if shutil.which("anew"):
                input_str = "\n".join(unique_param_urls)
                subprocess.run(["anew", all_paramspider_file], input=input_str, text=True)
                # Update the main all.urls.txt file as well
                subprocess.run(["anew", all_urls_file], input=input_str, text=True)
            else:
                # Python fallback for anew logic
                for target_file in [all_paramspider_file, all_urls_file]:
                    existing = set()
                    if os.path.exists(target_file):
                        with open(target_file, 'r') as f:
                            existing = set(l.strip() for l in f if l.strip())
                    
                    to_add = [u for u in unique_param_urls if u not in existing]
                    if to_add:
                        with open(target_file, 'a') as f:
                            f.write("\n".join(to_add) + "\n")
            
            logger.info(f"ParamSpider finished. Consolidated results into {all_paramspider_file}")
        else:
            logger.warning("No URLs discovered by ParamSpider.")

    except Exception as e:
        logger.error(f"Error executing ParamSpider: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 paramspider_enum.py "{{LIVE_SUBDOOMAINS_FILE}}" "{{CONTENT_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 paramspider_enum.py <subs_file> <output_path>")
        sys.exit(1)

    file_input = sys.argv[1]
    path_output = sys.argv[2]

    paramspider_enum(file_input, path_output)