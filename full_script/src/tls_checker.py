import json

def extract_tls_version(protocol_data, protocol_name):
    """
    Extracts the TLS version and server name from the protocol data.

    Args:
        protocol_data (dict): The data for a specific protocol.
        protocol_name (str): The name of the protocol (e.g., 'http', 'smtp').

    Returns:
        tuple: (tls_version (str or None), server_name (str))
    """
    if protocol_data.get('status') == 'success':
        if protocol_name == 'http':
            response = protocol_data.get('result', {}).get('response', {})
            request = response.get('request', {})
            tls_log = request.get('tls_log', {})
            handshake_log = tls_log.get('handshake_log', {})
            server_hello = handshake_log.get('server_hello', {})
            supported_versions = server_hello.get('supported_versions', {})
            tls_version = supported_versions.get('selected_version', {}).get('name', None) or \
                        server_hello.get('version', {}).get('name', None)
            server_name = request.get('host', 'unknown')
            return tls_version, server_name
        else:
            tls = protocol_data.get('result', {}).get('tls', {})
            handshake_log = tls.get('handshake_log', {})
            server_hello = handshake_log.get('server_hello', {})
            supported_versions = server_hello.get('supported_versions', {})
            tls_version = supported_versions.get('selected_version', {}).get('name', None) or \
                        server_hello.get('version', {}).get('name', None)
            return tls_version, server_hello.get('server_name', 'unknown')
    return None, None

def get_clean_tls_version(version):
    """
    Cleans and standardizes the TLS version string.

    Args:
        version (str): The raw TLS version string.

    Returns:
        str: The cleaned version string (e.g., '1.2').
    """
    if not version:
        return version
    cleaned = version.replace("v", " ").replace("V", " ").strip().split(" ")
    return cleaned[1]

def is_eol_tls(version):
    """
    Determines whether the given TLS version is end-of-life (EOL).

    Args:
        version (str): The TLS version string.

    Returns:
        tuple: (is_eol (bool), eol_date (str or None))
    """
    if version in ['1.0', '1.1']:
        return True, '2021-03-01'
    return False, None

def extract_tls_info(json_data):
    """
    Extracts TLS-related information from a list of JSON entries.

    Args:
        json_data (list): List of dictionaries parsed from JSON lines.

    Returns:
        list: List of dictionaries containing processed TLS information.
    """
    results = []

    for entry in json_data:
        if entry is None or not isinstance(entry, dict):
            continue

        ip = entry.get('ip')

        for protocol in ['http', 'smtp', 'imap', 'pop3', 'amqp091']:
            protocol_data = entry.get('data', {}).get(protocol, {})
            tls_version, server_name = extract_tls_version(protocol_data, protocol)
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
    """
    Processes a newline-delimited JSON file and writes extracted TLS info to an output file.

    Args:
        file_name (str): Path to the input JSON file.
        output_name (str): Path to the output JSON file to write results.
    """
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

    with open(output_name, 'w', encoding='utf-8') as outfile:
        json.dump(tls_info, outfile, indent=2)
