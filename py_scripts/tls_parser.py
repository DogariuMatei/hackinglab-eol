import json


def extract_tls_version(protocol_data):
    if protocol_data.get('status') == 'success':
        tls = protocol_data.get('result', {}).get('tls', {})
        handshake_log = tls.get('handshake_log', {})
        server_hello = handshake_log.get('server_hello', {})
        supported_versions = server_hello.get('supported_versions', {})
        tls_version = supported_versions.get('selected_version', {}).get('name', None) or \
                      server_hello.get('version', {}).get('name', None)
        return tls_version, server_hello.get('server_name', 'unknown')
    return None, None

def get_clean_tls_version(version):
    if not version:
        return version
    cleaned = version.replace("v", " ").replace("V", " ").strip().split(" ")
    return cleaned[1]


def is_eol_tls(version):
    if version in ['1.0', '1.1']:
        return True, '2021-03-01'
    return False, None


def extract_tls_info(json_data):
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')

        for protocol in ['http', 'smtp', 'imap', 'pop3', 'amqp091']:
            protocol_data = entry.get('data', {}).get(protocol, {})
            tls_version, server_name = extract_tls_version(protocol_data)
            clean_tls_version = get_clean_tls_version(tls_version)

            if tls_version:
                is_eol, eol_from = is_eol_tls(clean_tls_version)

                record = {
                    "ip": ip,
                    "server": server_name or "unknown",
                    "version": clean_tls_version,
                    "api_name": protocol.upper(),
                    "original_server": tls_version,
                    "is_eol": is_eol,
                    "eol_from": eol_from,
                    "status": f"EOL: {is_eol}, EOL Date: {eol_from or 'N/A'}"
                }

                results.append(record)

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