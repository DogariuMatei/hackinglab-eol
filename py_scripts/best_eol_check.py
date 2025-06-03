import json
import re
import requests
from urllib.parse import quote


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

    total_eol_hosts = 0
    successful_results: list[dict] = []
    failed_results: list[dict] = []
    print("Processing please stand by... \n\n")
    for entry in data:
        server_string = entry.get("server", "")
        ip           = entry.get("ip", "")

        if not server_string:
            continue

        # pull “Apache/2.4 … OpenSSL/1.1.1 …” into [(name, version), …]
        components = extract_valid_components(server_string)
        if not components:
            continue

        for server_name, version in components:
            api_name = check_and_replace_known_labels(server_name)

            api_result = check_eol_api(api_name, version)

            # common payload for *both* success & failure
            record = {
                "ip": ip,
                "server": server_name,
                "version": version,
                "api_name": api_name,
                "original_server": server_string,
            }

            if api_result.get("success"):
                record.update(
                    is_eol   = api_result.get("isEol"),
                    eol_from = api_result.get("eolFrom"),
                    status   = f"EOL: {api_result.get('isEol')}, "
                               f"EOL Date: {api_result.get('eolFrom') or 'N/A'}",
                )
                successful_results.append(record)
                if api_result.get("isEol"):
                    total_eol_hosts += 1
            else:
                # mirror the same keys, but flag the error
                record.update(
                    is_eol   = None,
                    eol_from = None,
                    status   = f"API lookup failed: {api_result.get('error', 'Unknown error')}",
                )
                failed_results.append(record)

    # sort both lists for readability (api_name → version → ip)
    successful_results.sort(key=lambda x: (x["api_name"].lower(),
                                           x["version"], x["ip"]))
    failed_results.sort(key=lambda x: (x["api_name"].lower(),
                                       x["version"], x["ip"]))

    all_results = successful_results.copy()
    all_results.extend(failed_results)

    return successful_results, failed_results, all_results, total_eol_hosts


def main():
    port = '993'

    # Input file path
    file_path = f'../data_matei/Port{port}/versions_transip_{port}.json'

    successful_results, failed_results, all_results, number_eol_hosts = process_json_file(file_path)

    # Save results to separate files
    all_results_file = f"../data_matei/Port{port}/all_eol_transip_{port}.json"
    with open(all_results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    success_file = f"../data_matei/Port{port}/eol_success_transip_{port}.json"
    with open(success_file, 'w', encoding='utf-8') as f:
        json.dump(successful_results, f, indent=2)

    failure_file = f"../data_matei/Port{port}/eol_fail_transip_{port}.json"
    with open(failure_file, 'w', encoding='utf-8') as f:
        json.dump(failed_results, f, indent=2)

    print(f"\nTotal Checked hosts: {len(all_results)}")
    print(f"\nSuccessful EOL checks: {len(successful_results)}")
    print(f"Failed EOL checks: {len(failed_results)} unique server name/version pairs")
    print(f"Total EOL hosts: {number_eol_hosts}")


if __name__ == "__main__":
    main()
