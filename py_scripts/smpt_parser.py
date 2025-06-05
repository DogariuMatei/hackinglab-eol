import json


def extract_server_info(json_data):
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')
        data = entry.get('data', {})
        smtp = data.get('smtp', {})

        # Skip entries with status other than "success"
        if smtp.get('status') != 'success':
            continue

        result = smtp.get('result', {})
        banner = result.get('banner', None)

        # Ensure banner exists
        if banner:
            try:
                # Extract server details for Exim/versionnumber format
                components = banner.split("ESMTP ")[1].split()
                if components and "Exim" in components[0]:
                    server_version = components[0] + "/" + components[1]
                    results.append({
                        "ip": ip,
                        "server": server_version
                    })
            except IndexError:
                continue

    return results


def process_file(file_name, output_name):
    with open(file_name, 'r') as file:
        json_data = []

        for line in file:
            line = line.strip()
            if line:
                try:
                    json_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    server_info = extract_server_info(json_data)

    print(f"Output for {file_name}:")
    print(json.dumps(server_info, indent=2))

    with open(output_name, 'w') as outfile:
        json.dump(server_info, outfile, indent=2)


# Process each file individually
process_file('AAS20857/zgrab_results/AS20857_25_results_27may.json', 'AAS20857/clean_version_ip/clean_versions_with_ip_AS20857_25.json')
process_file('AAS20857/zgrab_results/AS20857_587_results_27may.json', 'AAS20857/clean_version_ip/clean_versions_with_ip_AS20857_587.json')
process_file('AAS20857/zgrab_results/AS20857_465_results_27may.json', 'AAS20857/clean_version_ip/clean_versions_with_ip_AS20857_465.json')