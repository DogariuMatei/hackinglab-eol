import logging
import os
import subprocess
import re
from pathlib import Path

import netifaces

from process_registry import CHILD_PROCESSES_LOCK, CHILD_PROCESSES

logger = logging.getLogger(__name__)

def get_default_gateway_mac():
    gws = netifaces.gateways()
    default = gws.get('default')
    if not default or netifaces.AF_INET not in default:
        raise RuntimeError("No default gateway found")
    gateway_ip = default[netifaces.AF_INET][0]

    ip_neigh_output = subprocess.check_output(['ip', 'neigh'], text=True)

    for line in ip_neigh_output.splitlines():
        if gateway_ip in line and 'lladdr' in line:
            match = re.search(r'lladdr\s+([0-9a-f:]{17})', line)
            if match:
                return match.group(1)
    raise RuntimeError("Gateway MAC address not found in ARP table")


class Zmap:
    """
    Zmap scanner wrapper that runs scans and caches output based on input IPs and ports.
    """

    def __init__(self):
        self.cache_dir = "./cache/zmap"
        self.gateway_mac = get_default_gateway_mac()
        self.rate = 128

    def scan_ip_prefixes(self, file: str, port: int) -> str:
        """
        Runs a zmap scan on the given input file and port.

        Args:
            file (str): Path to a text file with IP prefixes.
            port (int): The port to scan.

        Returns:
            str: Path to the scan result file.

        Raises:
            Exception: If zmap fails or IO errors occur.
        """
        logger.info(f"Scanning with zmap on port {port}")

        output_file = Path(file).stem + f"-{port}.txt"
        output_path = os.path.join(self.cache_dir, output_file)

        if os.path.exists(output_path):
            logger.info("Using cached zmap output")
            return output_path

        os.makedirs(self.cache_dir, exist_ok=True)

        cmd = [
            "zmap",
            "-p", str(port),
            "-r", str(self.rate),
            "-w", file,
            "-G", self.gateway_mac,
            "-o", output_path
        ]

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            text=True
        )

        with CHILD_PROCESSES_LOCK:
            CHILD_PROCESSES.append(process)

        try:
            assert process.stderr is not None
            for line in process.stderr:
                logger.info(f"[zmap] {line.strip()}")
        finally:
            process.wait()
            with CHILD_PROCESSES_LOCK:
                if process in CHILD_PROCESSES:
                    CHILD_PROCESSES.remove(process)

        return output_path
