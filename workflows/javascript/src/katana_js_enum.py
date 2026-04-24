import os
import subprocess
import shutil
import tempfile
import logging
from urllib.parse import urlparse

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def host_from_url(url: str) -> str:
    """Consistently extracts the hostname for scope filtering."""
    url = url.strip()
    if not url or url.startswith("data:"):
        return ""
    if url.startswith("//"):
        url = "http:" + url
    if "://" not in url:
        url = "http://" + url
    try:
        parsed = urlparse(url)
        return (parsed.hostname or "").rstrip('.').lower()
    except Exception:
        return ""

def filter_by_subs(input_file, subs_set, output_file):
    """Filters lines in a file based on whether the URL host is in the subs_set."""
    if not os.path.exists(input_file):
        return
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as fin, \
        open(output_file, 'w', encoding='utf-8') as fout:
        for line in fin:
            host = host_from_url(line)
            if host and host in subs_set:
                fout.write(line.rstrip() + "\n")

def katana_js_enum(js_dir_path, all_js_file, subs_file, all_urls_file):
    """
    Crawls JS files with Katana, saves new URLs to the master list,
    and feeds newly discovered JS files back into the JS source list.
    """
    if not os.path.isfile(all_js_file):
        logger.error(f"JavaScript source file not found: {all_js_file}")
        return

    # Load subdomains for scope filtering
    subs_set = set()
    if os.path.isfile(subs_file):
        with open(subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subs_set = {line.strip().rstrip('.').lower() for line in f if line.strip() and not line.lstrip().startswith('#')}

    tmp_katana_path = None
    filtered_output_path = None

    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f_kat, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as f_filt:
            tmp_katana_path = f_kat.name
            filtered_output_path = f_filt.name

        logger.info(f"Running Katana deep-crawl on JavaScript files: {all_js_file}")
        
        # Optimized Katana command for speed and depth
        cmd = [
            "katana",
            "-list", all_js_file,
            "-jc",           # JS Crawling enabled
            "-d", "2",       # Recommended depth 2 to avoid infinite loops
            "-c", "30",
            "-p", "15",
            "-rl", "200",
            "-ct", "15m",    # Crawl Timeout
            "-mrs", "1000",  # Max Resource Size 1MB
            "-silent"
        ]

        with open(tmp_katana_path, 'w') as out_f:
            subprocess.run(cmd, stdout=out_f, stderr=subprocess.PIPE, text=True, check=False)

        if os.path.exists(tmp_katana_path) and os.path.getsize(tmp_katana_path) > 0:
            logger.info("Filtering Katana discoveries by subdomain scope...")
            
            if subs_set:
                filter_by_subs(tmp_katana_path, subs_set, filtered_output_path)
            else:
                shutil.copy(tmp_katana_path, filtered_output_path)

            if os.path.exists(filtered_output_path) and os.path.getsize(filtered_output_path) > 0:
                # 1. Update general URLs file
                logger.info(f"Syncing findings to master URL list: {all_urls_file}")
                if shutil.which("anew"):
                    with open(filtered_output_path, 'r') as f_in:
                        subprocess.run(["anew", all_urls_file], stdin=f_in)
                else:
                    with open(filtered_output_path, 'r') as f_in:
                        new_content = f_in.read()
                    with open(all_urls_file, 'a') as f_out:
                        f_out.write(new_content)

                # 2. Extract NEW JavaScript files from findings and feed back to all.javascript.txt
                logger.info(f"Extracting discovered JS files back to source list: {all_js_file}")
                new_js_found = []
                with open(filtered_output_path, 'r') as f_filt:
                    for line in f_filt:
                        url = line.strip()
                        # Detect if the URL is a JS file
                        if url.lower().split('?')[0].endswith('.js'):
                            new_js_found.append(url)
                
                if new_js_found:
                    logger.info(f"Found {len(new_js_found)} new JavaScript files in crawl results.")
                    logger.debug(f"New JS files: {new_js_found}")
                    if shutil.which("anew"):
                        subprocess.run(["anew", all_js_file], input="\n".join(new_js_found), text=True)
                    else:
                        with open(all_js_file, 'a') as f_js:
                            f_js.write("\n".join(new_js_found) + "\n")
                
                logger.info("Deep-crawl enumeration completed successfully.")
        else:
            logger.info("Katana found no additional URLs within these JS files.")

    except Exception as e:
        logger.error(f"Error executing Katana JS enumeration: {e}")

    finally:
        if tmp_katana_path and os.path.exists(tmp_katana_path): os.remove(tmp_katana_path)
        if filtered_output_path and os.path.exists(filtered_output_path): os.remove(filtered_output_path)

if __name__ == "__main__":
    import sys
    # Expected order from YAML:
    # python3 katana_js_enum.py <js_dir> <SELECTED_JS_FILES> <SUBDOMAIN_OUTPUT_FILE> <ALL_URLS_FILE>
    if len(sys.argv) < 5:
        print("Usage: python3 katana_js_enum.py <js_dir> <js_list_file> <subs_file> <all_urls_file>")
        sys.exit(1)

    katana_js_enum(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])