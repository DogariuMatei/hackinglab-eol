import json


def extract_tls_version(protocol_data):
    if protocol_data.get('status') == 'success':
        tls = protocol_data.get('result', {}).get('tls', {})
        handshake_log = tls.get('handshake_log', {})
        server_hello = handshake_log.get('server_hello', {})
        supported_versions = server_hello.get('supported_versions', {})
        tls_version = supported_versions.get('selected_version', {}).get('name', None) or server_hello.get('version',
                                                                                                           {}).get(
            'name', None)
        return tls_version


def extract_tls_info(json_data):
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')

        for protocol in ['http', 'smtp', 'imap', 'pop3']:
            protocol_data = entry.get('data', {}).get(protocol, {})
            tls_version = extract_tls_version(protocol_data)

            if tls_version:
                results.append({
                    "ip": ip,
                    "server": tls_version
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

    tls_info = extract_tls_info(json_data)

    print(f"Output for {file_name}:")
    print(json.dumps(tls_info, indent=2))

    with open(output_name, 'w', encoding='utf-8') as outfile:
        json.dump(tls_info, outfile, indent=2)


process_file('AAS20857/zgrab_results/AS20857_995_results_27may.json', 'AAS20857/clean_version_ip/clean_versions_with_ip_TLS_AS20857_995.json')