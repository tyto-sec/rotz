import os
import subprocess
import shutil
import tempfile
import logging
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def nuclei_js_scan(js_file, output_path, notify_enabled=False):
    """
    Runs Nuclei on a list of JavaScript files/URLs to find tokens, secrets, and exposures.
    js_file: Path to the file containing JS URLs (SELECTED_JS_FILES)
    output_path: The directory where results will be saved (JS_OUTPUT_PATH)
    """
    
    # 1. Validate Input File
    if not os.path.isfile(js_file):
        logger.error(f"JavaScript source file not found: {js_file}")
        return

    # 2. Setup Output Directory
    # Following project structure: output_path is JS_OUTPUT_PATH
    js_dir = os.path.abspath(output_path)
    final_output_file = os.path.join(js_dir, "nuclei.javascript.scan.txt")
    os.makedirs(js_dir, exist_ok=True)

    # 3. Check for Nuclei installation
    if not shutil.which("nuclei"):
        logger.error("Nuclei is not installed or not in PATH.")
        return

    logger.info(f"Starting Nuclei scan for JS vulnerabilities: {js_file}")

    try:
        # Create a temporary file for current run findings
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_output:
            tmp_output_path = tmp_output.name

        # 4. Execute Nuclei
        # -l: input file
        # -tags: specific JS/Secret templates
        # -o: output file
        cmd = [
            "nuclei",
            "-silent",
            "-l", js_file,
            "-tags", "js,secrets,exposure,token",
            "-o", tmp_output_path
        ]
        
        # Execute and wait
        subprocess.run(cmd, capture_output=False, text=True, check=False)

        # 5. Process Findings
        if os.path.exists(tmp_output_path) and os.path.getsize(tmp_output_path) > 0:
            with open(tmp_output_path, 'r') as f_tmp:
                new_findings = f_tmp.read().strip()
            
            if new_findings:
                logger.info(f"Nuclei found potential issues in JavaScript files.")
                
                # Update the master results file using anew
                if shutil.which("anew"):
                    with open(tmp_output_path, 'r') as f_in:
                        subprocess.run(["anew", final_output_file], stdin=f_in)
                else:
                    # Python fallback for anew
                    with open(final_output_file, 'a') as f_out:
                        f_out.write(new_findings + "\n")

                # 6. Notify if enabled
                if notify_enabled:
                    notify_config_path = os.path.expanduser("~/.config/notify/provider-config.yaml")
                    if shutil.which("notify") and os.path.isfile(notify_config_path):
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        notify_msg = f"[{timestamp}] Nuclei JS Findings\n\n{new_findings}"
                        try:
                            subprocess.run(
                                ["notify", "-bulk", "-provider", "telegram"],
                                input=notify_msg,
                                text=True,
                                capture_output=True
                            )
                        except Exception as ne:
                            logger.warning(f"Notification failed: {ne}")

        else:
            logger.info("Nuclei scan completed. No issues found.")

    except Exception as e:
        logger.error(f"Error during Nuclei execution: {e}")

    finally:
        # Cleanup
        if 'tmp_output_path' in locals() and os.path.exists(tmp_output_path):
            os.remove(tmp_output_path)

if __name__ == "__main__":
    import sys
    # Usage based on YAML vars: 
    # python3 nuclei_js_scan.py "{{SELECTED_JS_FILES}}" "{{JS_OUTPUT_PATH}}" "{{JS_NOTIFY}}"
    if len(sys.argv) < 3:
        print("Usage: python3 nuclei_js_scan.py <js_file> <output_path> [notify_enabled]")
        sys.exit(1)

    file_arg = sys.argv[1]
    out_arg = sys.argv[2]
    notify_arg = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    nuclei_js_scan(file_arg, out_arg, notify_arg)