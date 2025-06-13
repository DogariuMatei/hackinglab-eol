import json
import re

def extract_proftpd_info(json_data):
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')
        ftp_data = entry.get('data', {}).get('ftp', {})

        if ftp_data.get('status') == 'success':
            banner = ftp_data.get('result', {}).get('banner', '')
            if "ProFTPD" in banner:
                # Extract server info for ProFTPD
                parts = banner.split()
                server_name = "ProFTPD"
                server_version = None

                # Look for version
                if len(parts) >= 3 and parts[1] == "ProFTPD":
                    # If there's a version, format it appropriately
                    version = parts[2].strip('()')
                    if re.match(r'^\d+\.\d+\.\d+', version):
                        server_version = version.split('-')[0]

                # Create server info string
                server_info = f"{server_name}/{server_version}" if server_version else server_name
                results.append({
                    "ip": ip,
                    "server": server_info
                })

    return results


def process_file(file_name, output_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        json_data = []

        for line in file:
            line = line.strip()
            if line:
                try:
                    json_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    proftpd_info = extract_proftpd_info(json_data)

    print(f"Output for {file_name}:")
    print(json.dumps(proftpd_info, indent=2))

    with open(output_name, 'w', encoding='utf-8') as outfile:
        json.dump(proftpd_info, outfile, indent=2)


# process_file('AAS20857/zgrab_results/AS20857_21_results_27may.json', 'AAS20857/clean_version_ip/clean_versions_with_ip_AS20857_21.json')
