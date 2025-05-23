import json
import requests

INPUT_FILE = "../data_filip/AS57043/443/server_eol_success_AS57043.json"
OUTPUT_FILE = "../data_filip/AS57043/443/vulnerabilities_AS57043.json"

def get_vulnerabilities(vendor, product):
    url = f"https://cve.circl.lu/api/search/{vendor}/{product}"
    print(url)
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(data.cve_names)
            return data.get("data", [])
        else:
            print(f"Failed to fetch data for {vendor}/{product}. Status code: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching data for {vendor}/{product}: {e}")
        return []

def main():
    with open(INPUT_FILE, "r") as f:
        devices = json.load(f)

    if not isinstance(devices, list):
        devices = [devices]

    with open(OUTPUT_FILE, "w") as f:
        f.write("[\n")

    for i, device in enumerate(devices):
        if device.get("is_eol"):
            server = device.get("server", "").lower()
            vendor_product_map = {
                "apache": ("apache", "http_server"),
                "nginx": ("nginx", "nginx"),
                "iis": ("microsoft", "iis"),
            }
            vendor, product = vendor_product_map.get(server, (server, server))
            vulns = get_vulnerabilities(vendor, product)

            device["vulnerabilities"] = []
            for vuln in vulns:
                device["vulnerabilities"].append({
                    "id": vuln.get("id"),
                    "summary": vuln.get("summary"),
                    "cvss": vuln.get("cvss"),
                    "published": vuln.get("Published"),
                    "href": f"https://cve.circl.lu/api/cve/{vuln.get('id')}"
                })

        with open(OUTPUT_FILE, "a") as f:
            json.dump(device, f, indent=2)
            if i < len(devices) - 1:
                f.write(",\n")
            else:
                f.write("\n")

        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1} devices...")

    with open(OUTPUT_FILE, "a") as f:
        f.write("]\n")

if __name__ == "__main__":
    main()
