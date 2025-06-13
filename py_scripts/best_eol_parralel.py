import json
import re
import requests
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os

def check_and_replace_known_labels(server_name):
    mapping = {
        "Apache": "apache-http-server",
        "PHP": "php",
        "Python": "python",
        "OpenSSL": "openssl",
        "Microsoft-IIS": "windows-server",
        "Microsoft-HTTPAPI": "windows-server",
        "nginx": "nginx",
        "mod_python": "python",
        "mod_ssl": "openssl",
        "Exim": "exim",
        "ProFTPD": "proftpd",
        "Redis": "redis",
        "MongoDB": "mongodb",
        "MySQL": "mysql",
        "MariaDB": "mariadb",
        "MSSQL": "mssqlserver",
        "RabbitMQ": "rabbitmq",
    }
    return mapping.get(server_name, server_name)

keep_full_version = [
    "openssl",
    "proftpd",
]

def extract_valid_components(server_string):
    valid_components = []
    components = re.findall(r'(\w+(?:-\w+)?)\/(\d+(?:\.\d+)+(?:-\w+)?)', server_string)
    for name, version in components:
        name = name.strip()
        if '.' in version:
            api_name = check_and_replace_known_labels(name)
            if api_name.lower() in keep_full_version:
                valid_components.append((name, version))
                continue

            if api_name.lower() == "exim":
                match = re.match(r'^(\d+\.\d+)', version)
                if match:
                    valid_components.append((name, match.group(1)))
                continue

            if api_name.lower() == "proftpd":
                match = re.match(r'^(\d+\.\d+\.\d+)', version)
                if match:
                    valid_components.append((name, match.group(1)))
                continue

            version_parts = version.split('.')
            if len(version_parts) >= 2:
                simplified_version = f"{version_parts[0]}.{version_parts[1]}"
                valid_components.append((name, simplified_version))
    return valid_components

def check_eol_api(server_name, version):
    api_url = f"https://endoflife.date/api/v1/{quote('products')}/{quote(server_name)}/releases/{quote(version)}"
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            return {
                "isEol": result.get("isEol"),
                "eolFrom": result.get("eolFrom"),
                "success": True,
                "url": api_url
            }
        else:
            return {
                "error": f"FAILED: {response.status_code}",
                "url": api_url,
                "success": False
            }
    except Exception as e:
        return {
            "error": f"Exception: {str(e)}",
            "url": api_url,
            "success": False
        }

def process_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Prepare all ip/name/version combos to process
    tasks = []
    for entry in data:
        server_string = entry.get("server", "")
        ip = entry.get("ip", "")
        if not server_string:
            continue
        components = extract_valid_components(server_string)
        if not components:
            continue
        for server_name, version in components:
            api_name = check_and_replace_known_labels(server_name)
            tasks.append({
                "ip": ip,
                "server_name": server_name,
                "version": version,
                "api_name": api_name,
                "original_server": server_string
            })

    successful_results = []
    failed_results = []

    # Parallel API lookups
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_task = {}  # for postprocessing
        # Submit all jobs first
        for task in tasks:
            f = executor.submit(check_eol_from_cached_data, task["api_name"], task["version"])
            # f = executor.submit(check_eol_api, task["api_name"], task["version"])
            future_to_task[f] = task

        # Use tqdm for progress bar
        for f in tqdm(as_completed(future_to_task), total=len(tasks), desc="API lookups"):
            task = future_to_task[f]
            api_result = f.result()

            record = {
                "ip": task["ip"],
                "server": task["server_name"],
                "version": task["version"],
                "api_name": task["api_name"],
                "original_server": task["original_server"],
            }

            if api_result.get("success"):
                record.update(
                    is_eol=api_result.get("isEol"),
                    eol_from=api_result.get("eolFrom"),
                    status=f"EOL: {api_result.get('isEol')}, "
                           f"EOL Date: {api_result.get('eolFrom') or 'N/A'}",
                )
                successful_results.append(record)
            else:
                record.update(
                    is_eol=None,
                    eol_from=None,
                    status=f"API lookup failed: {api_result.get('error', 'Unknown error')}",
                )
                failed_results.append(record)

    successful_results.sort(key=lambda x: (x["api_name"].lower(), x["version"], x["ip"]))
    failed_results.sort(key=lambda x: (x["api_name"].lower(), x["version"], x["ip"]))

    return successful_results, failed_results

EOL_CACHE_DIR = "./cache/eol"

def get_cache_path(product):
    return os.path.join(EOL_CACHE_DIR, f"{product}.json")

# TODO: use https://endoflife.date/api/{product}.json"

product_cache = {}

def load_product_data(product):
    """Load product data from cache or fetch if not cached."""
    product = product.lower()
    if product in product_cache:
        return product_cache[product]

    os.makedirs(EOL_CACHE_DIR, exist_ok=True)
    cache_path = get_cache_path(product)

    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(data)
    else:
        url = f"https://endoflife.date/api/v1/products/{quote(product)}"
        # url = f"https://endoflife.date/api/{quote(product)}.json"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            return []

    product_cache[product] = data
    return data

def check_eol_from_cached_data(server_name, version):
    if load_product_data(server_name) == []:
        return { "sucess": False }
    product_data = (load_product_data(server_name)).get("result", {}).get("releases", [])
    for release in product_data:
        if release.get("name") == version:
            return {
                "isEol": release.get("isEol"),
                "eolFrom": release.get("eolFrom"),
                "success": True,
                "url": f"https://endoflife.date/{quote(server_name)}"
            }

    return {
        "success": False,
        "error": f"Version {version} not found in product data",
        "url": f"https://endoflife.date/api/{quote(server_name)}.json"
    }


def process_file(file_name, success_file, failure_file):
    successful_results, failed_results = process_json_file(file_name)

    with open(success_file, 'w', encoding='utf-8') as f:
        json.dump(successful_results, f, indent=2)

    with open(failure_file, 'w', encoding='utf-8') as f:
        json.dump(failed_results, f, indent=2)

    print(f"\nSuccessful EOL checks: {len(successful_results)}")
    print(f"Failed EOL checks: {len(failed_results)} unique server name/version pairs")
