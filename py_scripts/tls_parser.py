import json

def extract_tls_info(json_data):
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')
        data = entry.get('data', {})
        imap = data.get('imap', {})

        # Skip entries with status other than "success"
        if imap.get('status') != 'success':
            continue

        result = imap.get('result', {})
        tls = result.get('tls', {})
        handshake_log = tls.get('handshake_log', {})
        server_hello = handshake_log.get('server_hello', {})
        version = server_hello.get('version', {})
        tls_version = version.get('name')

        # Ensure TLS version exists
        if tls_version:
            results.append({
                "ip": ip,
                "tls_version": tls_version
            })

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

    tls_info = extract_tls_info(json_data)

    print(f"Output for {file_name}:")
    print(json.dumps(tls_info, indent=2))

    with open(output_name, 'w') as outfile:
        json.dump(tls_info, outfile, indent=2)


# Process each file individually
process_file('../zgrab_results.json', '../data_matei/Port993/versions_transip_993.json')
# process_file('AS20857/zgrab_results/AS20857_993_results.json', 'AS20857/clean_version_ip/clean_tls_versions_AS20857_993.json')