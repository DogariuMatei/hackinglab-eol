import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import List

from .base import VersionScanner
from process_registry import CHILD_PROCESSES_LOCK, CHILD_PROCESSES
from typing import Callable
from typing import Optional
import json
import re

logger = logging.getLogger(__name__)

class ZGrab2(VersionScanner):
    """
    Wrapper around the zgrab2 command-line scanner.
    """

    def __init__(self, command: List[str], port: int, version_extractor: Optional[Callable[[object], Optional[tuple[str, str]]]] = None):
        self.cache_dir = "./cache/version-scanner/zgrab2"
        self.command = command
        self.senders = 20
        self.port = port
        self.version_extractor = version_extractor

    def scan_versions(self, ips_file: str) -> str:
        os.makedirs(self.cache_dir, exist_ok=True)

        file_stem = Path(ips_file).stem
        output_path = os.path.join(self.cache_dir, f"{file_stem}.txt")

        if os.path.exists(output_path):
            logger.info("Using cached zgrab2 output")
            return output_path

        args = self.command.copy()
        args.insert(0, "--senders")
        args.insert(1, str(self.senders))
        args.extend([
            "--output-file", output_path,
            "--port", str(self.port),
            # "-t", "5"
        ])

        process = subprocess.Popen(
            ["zgrab2"] + args,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        with CHILD_PROCESSES_LOCK:
            CHILD_PROCESSES.append(process)

        def log_stderr(stderr):
            for line in stderr:
                logger.info(f"[zgrab2] {line.strip()}")

        stderr_thread = threading.Thread(target=log_stderr, args=(process.stderr,))
        stderr_thread.start()

        try:
            assert process.stdin is not None
            with open(ips_file, "r") as f:
                for line in f:
                    process.stdin.write(line.strip() + "\n")
            process.stdin.close()

            process.wait()
            stderr_thread.join()

        finally:
            with CHILD_PROCESSES_LOCK:
                if process in CHILD_PROCESSES:
                    CHILD_PROCESSES.remove(process)

        self.extract_versions_from_output(output_path, output_path.replace(".txt", ".json"))
        return output_path

    def extract_versions_from_output(self, output_path: str, save_path: str):
        extracted_pairs = []

        if self.version_extractor is not None:
            with open(output_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        return None

                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        return None

                    try:
                        extracted = self.version_extractor(entry)
                        if extracted is not None:
                            extracted_pairs.append(extracted)
                    except Exception as e:
                        logger.warning(f"Failed to extract version from line: {line!r} — {e}")

            dicts = [{"ip": ip, "server": version} for ip, version in extracted_pairs]

            try:
                with open(save_path, 'w', encoding='utf-8') as out_file:
                    json.dump(dicts, out_file, indent=4)
                logger.info(f"Saved {len(dicts)} extracted entries to {save_path}")
            except Exception as e:
                logger.error(f"Failed to write extracted results to file: {e}")

def http_version_extractor(entry) -> Optional[tuple[str, str]]:
    headers = entry.get('data', {}).get('http', {}).get('result', {}).get('response', {}).get('headers', {})
    server = headers.get('server')

    # select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
    if server is not None and len(server) > 0 and server[0] is not None:
        # Get IP address
        ip = entry.get('ip')
        return (ip, server[0])

    return None

def smtp_version_extractor(entry) -> Optional[tuple[str, str]]:
    ip = entry.get('ip')
    data = entry.get('data', {})
    smtp = data.get('smtp', {})

    # Skip entries with status other than "success"
    if smtp.get('status') != 'success':
        return None

    result = smtp.get('result', {})
    banner = result.get('banner', None)

    # Ensure banner exists
    if banner:
        try:
            # Extract server details for Exim/versionnumber format
            components = banner.split("ESMTP ")[1].split()
            if components and "Exim" in components[0]:
                server_version = components[0] + "/" + components[1]
                return (ip, server_version)
        except IndexError:
            return None
    return None

def ftp_version_extractor(entry) -> Optional[tuple[str, str]]:
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
            return (ip, server_info)

    return None

def mssql_version_extractor(entry) -> Optional[tuple[str, str]]:
    ip = entry.get("ip")
    data = entry.get("data", {}).get("mssql", {})
    status = data.get("status")
    result = data.get("result", {})
    version = result.get("version")

    if status == "success" and version and re.match(r'^\d+(\.\d+)+$', version):
        server_val = f"MSSQL/{version}"
        return (ip, server_val)

    return None

def rabbitmq_version_extractor(entry) -> Optional[tuple[str, str]]:
    ip = entry.get('ip')
    amqp_data = entry.get('data', {}).get('amqp091', {})

    if amqp_data.get('status') == 'success':
        server_props = amqp_data.get('result', {}).get('server_properties', {})
        product = server_props.get('product')
        version = server_props.get('version')

        if product == 'RabbitMQ' and version:
            server_info = f"{product}/{version}"
            return (ip, server_info)

    return None
