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

def jsscanner_enum(input_file, output_path, regex_file):
    """
    Python wrapper for JSScanner.
    input_file: The file containing JS URLs (e.g., all.javascript.txt)
    output_path: The base content directory
    regex_file: Path to the JSScanner Regex.txt file
    """
    
    # 1. Validate Input File
    if not os.path.isfile(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    # 2. Validate Regex File
    # Check provided path, then common /opt paths as fallback
    if not os.path.isfile(regex_file):
        potential_paths = [
            regex_file,
            "/opt/JSScanner/Regex.txt",
            "/opt/JSScanner/regex.txt"
        ]
        found = False
        for p in potential_paths:
            if os.path.isfile(p):
                regex_file = p
                found = True
                break
        if not found:
            logger.error(f"Regex file not found at {regex_file} or /opt/JSScanner/")
            return

    # 3. Validate JSScanner.py
    jsscanner_script = "/opt/JSScanner/JSScanner.py"
    if not os.path.isfile(jsscanner_script):
        logger.error(f"JSScanner not found at {jsscanner_script}")
        return

    # 4. Setup Output Directory
    # Following project structure: output_path is JS_OUTPUT_PATH
    js_dir = os.path.abspath(output_path)
    os.makedirs(js_dir, exist_ok=True)
    
    final_output_txt = os.path.join(js_dir, "output.txt")
    final_content_txt = os.path.join(js_dir, "jsscanner.content.txt")

    # Resolve absolute paths for the scanner
    abs_input = os.path.realpath(input_file)
    abs_regex = os.path.realpath(regex_file)

    logger.info(f"Running JSScanner on: {abs_input}")

    # 5. Execute JSScanner in a temporary directory
    # JSScanner writes a file named 'output.txt' in the CWD
    try:
        with tempfile.TemporaryDirectory() as work_dir:
            input_str = f"{abs_input}\n{abs_regex}\n"
            
            # Run JSScanner.py using Python 3
            # We capture output to jsscanner.content.txt
            with open(final_content_txt, 'w') as log_file:
                process = subprocess.run(
                    ["python3", jsscanner_script],
                    input=input_str,
                    cwd=work_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False
                )

            # Check if JSScanner created its specific output.txt
            tmp_output_txt = os.path.join(work_dir, "output.txt")
            if os.path.exists(tmp_output_txt):
                shutil.move(tmp_output_txt, final_output_txt)
                logger.info(f"JSScanner completed. Results saved to {final_output_txt}")
            else:
                logger.warning("JSScanner execution finished but no output.txt was generated.")

    except Exception as e:
        logger.error(f"Error executing JSScanner: {e}")

if __name__ == "__main__":
    import sys
    # Usage based on YAML vars: 
    # python3 jsscanner_enum.py "{{SELECTED_JS_FILES}}" "{{JS_OUTPUT_PATH}}" "{{JS_REGEX_FILE}}"
    if len(sys.argv) < 4:
        print("Usage: python3 jsscanner_enum.py <input_file> <output_path> <regex_file>")
        sys.exit(1)

    input_arg = sys.argv[1]
    output_arg = sys.argv[2]
    regex_arg = sys.argv[3]

    jsscanner_enum(input_arg, output_arg, regex_arg)