import json
import re
import requests
from urllib.parse import quote
import concurrent.futures
import time
from functools import lru_cache
from tqdm import tqdm  # Optional: for progress bar


# LRU cache to avoid duplicate API calls for the same server/version combination
@lru_cache(maxsize=1000)
def check_eol_api(server_name, version):
    api_url = f"https://endoflife.date/api/v1/{quote('products')}/{quote(server_name)}/releases/{quote(version)}"
    try:
        response = requests.get(api_url, timeout=5)
        print(response)

        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            return {
                "isEol": result.get("isEol"),
                "eolFrom": result.get("eolFrom")
            }
        else:
            return {
                "error": f"FAILED: {response.status_code}",
                "url": api_url
            }
    except Exception as e:
        return {
            "error": f"Exception: {str(e)}",
            "url": api_url
        }


def check_and_replace_known_labels(server_name):
    if server_name == "Apache":
        return "apache-http-server"
    else:
        return server_name


def parse_server_string(server_string):
    if '/' in server_string:
        parts = server_string.split('/', 1)
        server_name = check_and_replace_known_labels(parts[0].strip())

        # Initialize version with a default value
        version = "unknown"

        version_match = re.search(r'(\d+\.\d+)', parts[1])
        if version_match:
            version = version_match.group(1)
        else:
            version_match = re.search(r'(\d+)', parts[1])
            if version_match:
                version = version_match.group(1)

        return (server_name, version)
    return (server_string, "unknown")  # Return the server name without version if no slash


# Process a single entry
def process_entry(entry):
    server_string = entry.get("server", "")
    ip = entry.get("ip", "")

    if not server_string:
        return None

    server_tuple = parse_server_string(server_string)
    if server_tuple is None:
        return None

    server_name, version = server_tuple

    # Check EOL status
    api_result = check_eol_api(server_name, version)

    if "error" in api_result:
        status = f"Error: {api_result['error']}"
    else:
        is_eol = api_result.get("isEol")
        eol_from = api_result.get("eolFrom")
        status = f"EOL: {is_eol}, EOL Date: {eol_from if eol_from else 'N/A'}"

    # Create result with IP included
    return {
        "ip": ip,
        "server": server_name,
        "version": version,
        "original_server": server_string,
        "is_eol": api_result.get("isEol") if "error" not in api_result else None,
        "eol_from": api_result.get("eolFrom") if "error" not in api_result else None,
        "status": status
    }


def main():
    start_time = time.time()

    # Input file from the previous script
    file_path = 'clean_versions_with_ip_80.json'
    output_file = "server_eol_with_ip.json"

    # Load data
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    print(f"Processing {len(data)} entries...")

    # Process data in parallel
    results = []

    # Use ThreadPoolExecutor for parallel API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Submit all tasks
        future_to_entry = {executor.submit(process_entry, entry): entry for entry in data}

        # Process results as they complete (with optional progress bar)
        for future in tqdm(concurrent.futures.as_completed(future_to_entry), total=len(data), desc="Processing"):
            result = future.result()
            if result:
                results.append(result)

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    elapsed_time = time.time() - start_time
    print(f"\nProcessed {len(results)} server entries in {elapsed_time:.2f} seconds")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()