import json
import re
import requests
from urllib.parse import quote


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


def process_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    results = []
    for entry in data:
        server_string = entry.get("server", "")
        ip = entry.get("ip", "")

        if server_string:
            server_tuple = parse_server_string(server_string)
            if server_tuple is not None:
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
                results.append({
                    "ip": ip,
                    "server": server_name,
                    "version": version,
                    "original_server": server_string,
                    "is_eol": api_result.get("isEol") if "error" not in api_result else None,
                    "eol_from": api_result.get("eolFrom") if "error" not in api_result else None,
                    "status": status
                })

    return results


def main():
    # Input file from the previous script
    file_path = 'clean_versions_with_ip_80.json'

    # Process file and get results with EOL information
    results = process_json_file(file_path)

    # Save results
    output_file = "server_eol_with_ip.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\nProcessed {len(results)} server entries")
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()