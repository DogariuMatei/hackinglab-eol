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

        version_match = re.search(r'(\d+\.\d+)', parts[1])
        if version_match:
            version = version_match.group(1)
        else:
            version_match = re.search(r'(\d+)', parts[1])
            if version_match:
                version = version_match.group(1)

        return (server_name, version)
    return None


def process_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    result = set()
    for entry in data:
        server_string = entry.get("server", "")
        ip = entry.get("ip", "")
        if server_string:
            server_tuple = parse_server_string(server_string)
            if server_tuple is not None:
                # result.add((server_tuple[0], server_tuple[1], ip))
                result.add((server_tuple[0], server_tuple[1]))

    return result



def check_eol_api(server_name, version):
    api_url = f"https://endoflife.date/api/v1/{quote('products')}/{quote(server_name)}/releases/{quote(version)}"
    response = requests.get(api_url, timeout=5)

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




def main():
    # TODO CHANGE ME TO YOUR FILE PATH
    # THIS IS THE FILE CONTAINING SERVERS AND VERSIONS NOT THE COUNT ONE!!!!!
    file_path = 'clean_versions.json'

    servers_info = process_json_file(file_path)

    results = []

    for server_name, version in servers_info:
    # for server_name, version, ip in servers_info:
        api_result = check_eol_api(server_name, version)

        if "error" in api_result:
            status = f"Error: {api_result['error']}"
        else:
            is_eol = api_result.get("isEol")
            eol_from = api_result.get("eolFrom")
            status = f"EOL: {is_eol}, EOL Date: {eol_from if eol_from else 'N/A'}"

        results.append({
            "server": server_name,
            "version": version,
            "is_eol": api_result.get("isEol") if "error" not in api_result else None,
            "eol_from": api_result.get("eolFrom") if "error" not in api_result else None,
            "status": status
        })
        # results.append({
        #     "ip": ip,
        #     "server": server_name,
        #     "version": version,
        #     "is_eol": api_result.get("isEol") if "error" not in api_result else None,
        #     "eol_from": api_result.get("eolFrom") if "error" not in api_result else None,
        #     "status": status
        # })


    output_file = "server_eol_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()