import os
import subprocess
import shutil
import tempfile
import logging
from urllib.parse import urlparse

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def host_from_url(url: str) -> str:
    """Extracts the hostname from a URL consistently."""
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

def subjs_enum(urls_file, output_path, subs_file=None):
    if not os.path.isfile(urls_file):
        logger.error(f"URLs file not found: {urls_file}")
        return

    # Directory setup based on YAML
    js_dir = os.path.abspath(output_path)
    all_js_file = os.path.join(js_dir, "all.javascript.txt")
    os.makedirs(js_dir, exist_ok=True)

    # Load subdomains for filtering (Mandatory passed via arg)
    subs_set = set()
    if subs_file and os.path.isfile(subs_file):
        logger.info(f"Loading subdomains from: {subs_file}")
        with open(subs_file, 'r', encoding='utf-8', errors='ignore') as f:
            subs_set = {line.strip().rstrip('.').lower() for line in f if line.strip() and not line.lstrip().startswith('#')}
    else:
        logger.warning("No valid subdomains file provided for filtering.")

    try:
        # Generate temporary files
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f_in_tmp, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as f_subjs_tmp:
            
            filtered_input_path = f_in_tmp.name
            tmp_js_path = f_subjs_tmp.name

        # 1. Filter input URLs
        if subs_set:
            logger.info(f"Filtering input URLs based on {len(subs_set)} subdomains...")
            filter_by_subs(urls_file, subs_set, filtered_input_path)
        else:
            shutil.copy(urls_file, filtered_input_path)

        # 2. Run subjs
        if not shutil.which("subjs"):
            logger.error("subjs is not installed or not in PATH.")
            return

        logger.info("Running subjs to discover JavaScript files...")
        with open(filtered_input_path, 'r') as fin:
            # We use subprocess.run with capture_output to handle large stdin/stdout properly
            result = subprocess.run(["subjs"], stdin=fin, capture_output=True, text=True, check=False)
            
            if result.stdout:
                # Save results to temp file
                lines = sorted(list(set(result.stdout.splitlines())))
                with open(tmp_js_path, 'w') as f_tmp:
                    f_tmp.write("\n".join(lines) + "\n")

        # 3. Consolidate and filter results
        if os.path.exists(tmp_js_path) and os.path.getsize(tmp_js_path) > 0:
            final_set = set()
            
            # Filter what we just discovered
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f_filt_tmp:
                filter_by_subs(tmp_js_path, subs_set, f_filt_tmp.name)
                f_filt_tmp.close()
                if os.path.exists(f_filt_tmp.name):
                    with open(f_filt_tmp.name, 'r') as f:
                        final_set.update(l.strip() for l in f if l.strip())
                    os.remove(f_filt_tmp.name)

            # Filter existing master file
            if os.path.exists(all_js_file) and os.path.getsize(all_js_file) > 0:
                with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f_ext_tmp:
                    filter_by_subs(all_js_file, subs_set, f_ext_tmp.name)
                    f_ext_tmp.close()
                    if os.path.exists(f_ext_tmp.name):
                        with open(f_ext_tmp.name, 'r') as f:
                            final_set.update(l.strip() for l in f if l.strip())
                        os.remove(f_ext_tmp.name)

            if final_set:
                sorted_js = sorted(list(final_set))
                with open(all_js_file, 'w') as f_out:
                    f_out.write("\n".join(sorted_js) + "\n")
                logger.info(f"Saved {len(sorted_js)} unique JS URLs to {all_js_file}")
            else:
                logger.info("No JavaScript URLs remained after subdomain filtering.")
        else:
            logger.info("subjs found no JavaScript files.")

    except Exception as e:
        logger.error(f"Error during subjs enumeration: {e}")

    finally:
        if os.path.exists(filtered_input_path): os.remove(filtered_input_path)
        if os.path.exists(tmp_js_path): os.remove(tmp_js_path)

if __name__ == "__main__":
    import sys
    # Usage from YAML: python3 subjs_enum.py '{{JS_URLS_FILE}}' '{{JS_OUTPUT_PATH}}' '{{SUBDOMAIN_OUTPUT_FILE}}'
    if len(sys.argv) < 3:
        print("Usage: python3 subjs_enum.py <urls_file> <output_path> [subs_file]")
        sys.exit(1)

    urls_p = sys.argv[1]
    out_p = sys.argv[2]
    subs_p = sys.argv[3] if len(sys.argv) > 3 else None

    subjs_enum(urls_p, out_p, subs_p)