import os
import subprocess
import shutil
import json
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def gowitness_enum(subs_file, output_path):
    # Check whether the subdomains file exists
    if not os.path.isfile(subs_file):
        logger.error(f"Subdomains file not found: {subs_file}")
        return

    base_output = os.path.abspath(output_path)
    enum_dir = os.path.join(base_output, "enum")
    
    csv_file = os.path.join(enum_dir, "gowitness.enum.subs.csv")
    jsonl_file = os.path.join(enum_dir, "gowitness.enum.subs.jsonl")
    json_result_file = os.path.join(enum_dir, "gowitness.enum.subs.json")
    
    os.makedirs(enum_dir, exist_ok=True)

    logger.info(f"Starting gowitness enumeration for: {subs_file}")
    
    try:
        # Modern User-Agent to help bypass blocks
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        
        # Build command
        # Note: --screenshot-skip-save is used because this module focuses on data enumeration (CSV/JSON)
        cmd = [
            "gowitness", "scan", "file",
            "-f", subs_file,
            "--write-csv", "--write-csv-file", csv_file,
            "--write-jsonl", "--write-jsonl-file", jsonl_file,
            "--screenshot-skip-save",
            "--chrome-user-agent", user_agent,
            "--threads", "10",
            "--timeout", "30",
            "--delay", "3"
        ]
        
        # Execute gowitness
        result = subprocess.run(cmd, capture_output=False, text=True, check=False)
        
        if result.returncode != 0:
            logger.error(f"Gowitness exited with error code {result.returncode}")

        # Post-processing: Convert JSONL to a single JSON array (mimicking jq -s)
        if os.path.exists(jsonl_file) and os.path.getsize(jsonl_file) > 0:
            logger.info(f"Converting JSONL to structured JSON: {json_result_file}")
            json_array = []
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        json_array.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            
            with open(json_result_file, 'w', encoding='utf-8') as f:
                json.dump(json_array, f, indent=4)
        else:
            logger.warning("No enumeration data was generated (JSONL file is empty or missing).")

    except Exception as e:
        logger.error(f"Error during gowitness enumeration: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML: python3 gowitness_enum.py '{{LIVE_SUBDOOMAINS_FILE}}' '{{CONTENT_OUTPUT_PATH}}'
    if len(sys.argv) < 3:
        print("Usage: python3 gowitness_enum.py <subs_file> <output_path>")
        sys.exit(1)

    file_input = sys.argv[1]
    path_output = sys.argv[2]

    gowitness_enum(file_input, path_output)