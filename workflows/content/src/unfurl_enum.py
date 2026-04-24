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

def unfurl_enum(cleaned_urls_file, output_path):
    # Check if the cleaned URLs file exists
    if not os.path.isfile(cleaned_urls_file):
        logger.error(f"Cleaned URLs file not found: {cleaned_urls_file}")
        return

    # Setup paths based on project structure
    base_output = os.path.abspath(output_path)
    wordlists_dir = os.path.join(base_output, "wordlists")
    
    # Navigation to find subs directory (usually adjacent to content)
    # Replicating logic: output/tesla/content -> output/tesla/subs
    project_root = os.path.dirname(base_output)
    all_subs_file = os.path.join(project_root, "subs", "all.subs.txt")
    
    os.makedirs(wordlists_dir, exist_ok=True)

    # Map of unfurl modes to target output files
    extractions = {
        "keys": os.path.join(wordlists_dir, "all.keys.txt"),
        "values": os.path.join(wordlists_dir, "all.values.txt"),
        "keypairs": os.path.join(wordlists_dir, "all.keypairs.txt"),
        "domains": os.path.join(wordlists_dir, "all.domains.txt"),
        "apexes": os.path.join(wordlists_dir, "all.apex.txt"),
        "paths": os.path.join(wordlists_dir, "all.paths.txt")
    }

    logger.info(f"Extracting data using unfurl from: {cleaned_urls_file}")

    try:
        # Check if unfurl is installed
        if not shutil.which("unfurl"):
            logger.error("unfurl is not installed or not in PATH. Please install it with 'go install github.com/tomnomnom/unfurl@latest'.")
            return

        # Read the cleaned URLs content
        with open(cleaned_urls_file, 'r', encoding='utf-8', errors='ignore') as f_in:
            urls_content = f_in.read()

        if not urls_content.strip():
            logger.warning("Cleaned URLs file is empty. Nothing to unfurl.")
            return

        for mode, target_path in extractions.items():
            logger.info(f"Extracting {mode}...")
            
            # Execute unfurl: cat cleaned_urls | unfurl -u <mode>
            cmd = ["unfurl", "-u", mode]
            result = subprocess.run(cmd, input=urls_content, capture_output=True, text=True, check=False)
            
            if result.stdout.strip():
                # Use anew to keep lists unique and sorted
                if shutil.which("anew"):
                    subprocess.run(["anew", target_path], input=result.stdout, text=True)
                else:
                    # Fallback logic for anew
                    discovered = set(result.stdout.splitlines())
                    existing = set()
                    if os.path.exists(target_path):
                        with open(target_path, 'r') as f:
                            existing = set(l.strip() for l in f if l.strip())
                    
                    to_add = [line for line in discovered if line not in existing]
                    if to_add:
                        with open(target_path, 'a') as f_out:
                            f_out.write("\n".join(to_add) + "\n")

        # Post-extraction: Update master subdomains with domains newly found in URLs
        extracted_domains_file = extractions["domains"]
        if os.path.exists(extracted_domains_file) and os.path.getsize(extracted_domains_file) > 0:
            logger.info(f"Syncing extracted domains back to master subdomains list...")
            if shutil.which("anew"):
                with open(extracted_domains_file, 'r') as f_ext:
                    subprocess.run(["anew", all_subs_file], stdin=f_ext)
            else:
                with open(extracted_domains_file, 'r') as f_ext:
                    new_domains = f_ext.read()
                    with open(all_subs_file, 'a') as f_subs:
                        f_subs.write(new_domains)

    except Exception as e:
        logger.error(f"Error during unfurl enumeration: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 unfurl_enum.py "{{CLEANED_URLS_FILE}}" "{{CONTENT_OUTPUT_PATH}}"
    if len(sys.argv) < 3:
        print("Usage: python3 unfurl_enum.py <cleaned_urls_file> <output_path>")
        sys.exit(1)

    urls_input = sys.argv[1]
    output_dir = sys.argv[2]
    
    unfurl_enum(urls_input, output_dir)