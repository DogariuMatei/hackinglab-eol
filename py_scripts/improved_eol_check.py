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

    }
    return mapping.get(server_name, server_name)


keep_full_version = [
    "openssl",

]


def extract_valid_components(server_string):
    """Extract components that have at least major.minor version format (x.y)"""
    valid_components = []

    # Find all name/version patterns in the string
    components = re.findall(r'(\w+(?:-\w+)?)\/(\d+(?:\.\d+)+(?:-\w+)?)', server_string)

    # Only keep components with at least major.minor version format
    # Only keep components with at least major.minor version format
    for name, version in components:
        name = name.strip()
        # Check if version has at least one dot (x.y format)
        if '.' in version:
            # Map name to API name for checking against keep_full_version list
            api_name = check_and_replace_known_labels(name)

            # Keep the full version string for specific software
            if api_name.lower() in keep_full_version:
                valid_components.append((name, version))
                continue

            # For others, extract just the major.minor part (x.y)
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
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    successful_results = []
    # Use a set to track unique failed (server_name, version) pairs
    failed_pairs = set()

    for entry in data:
        server_string = entry.get("server", "")
        ip = entry.get("ip", "")

        if server_string:
            # Extract valid components from the server string
            components = extract_valid_components(server_string)

            if components:
                # Process each valid component
                for server_name, version in components:
                    # Map the server name to the correct API label
                    api_name = check_and_replace_known_labels(server_name)

                    # Check EOL status
                    api_result = check_eol_api(api_name, version)

                    # Add to appropriate collection based on success/failure
                    if api_result.get("success", False):
                        # Successful API call
                        successful_results.append({
                            "ip": ip,
                            "server": server_name,
                            "version": version,
                            "api_name": api_name,
                            "original_server": server_string,
                            "is_eol": api_result.get("isEol"),
                            "eol_from": api_result.get("eolFrom"),
                            "status": f"EOL: {api_result.get('isEol')}, EOL Date: {api_result.get('eolFrom') if api_result.get('eolFrom') else 'N/A'}"
                        })
                    else:
                        # Failed API call - just add the (server_name, version) pair to the set
                        failed_pairs.add((api_name, version))

    # Convert the set of failed pairs to a list of dictionaries for JSON serialization
    failed_results = [{"server_name": pair[0], "version": pair[1]} for pair in failed_pairs]

    # Sort alphabetically by server_name and then version for easier readability
    failed_results.sort(key=lambda x: (x["server_name"], x["version"]))

    return successful_results, failed_results


def main():
    # Input file path
    file_path = '../data_matei/clean_versions_for_konstantin_zgrab_targets.json'

    # Process file and get results with EOL information
    successful_results, failed_results = process_json_file(file_path)

    # Save results to separate files
    success_file = "../data_matei/server_eol_success_for_konstantin_zgrab_targets.json"
    with open(success_file, 'w', encoding='utf-8') as f:
        json.dump(successful_results, f, indent=2)

    failure_file = "../data_matei/server_eol_failure_for_konstantin_zgrab_targets.json"
    with open(failure_file, 'w', encoding='utf-8') as f:
        json.dump(failed_results, f, indent=2)

    print(f"\nSuccessful EOL checks: {len(successful_results)}")
    print(f"Failed EOL checks: {len(failed_results)} unique server name/version pairs")


if __name__ == "__main__":
    main()