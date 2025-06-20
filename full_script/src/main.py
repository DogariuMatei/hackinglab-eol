import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List
import sys
import signal
import subprocess

from asn_lookup import CachedAsnLookup, HackerTargetAPI, validate_asn
from zmap import Zmap
from version_scanners import VersionScanner, ZGrab2, MySQLScanner, RedisScanner, MongoDbScanner
from process_registry import CHILD_PROCESSES_LOCK, CHILD_PROCESSES
from version_scanners.zgrab import ftp_version_extractor, http_version_extractor, mssql_version_extractor, rabbitmq_version_extractor, smtp_version_extractor
import eol_checker
import cve_finder
import tls_checker

logger = logging.getLogger(__name__)



def build_scanner_map() -> Dict[int, List[VersionScanner]]:
    scanner_map: Dict[int, List[VersionScanner]] = {}

    scanner_map[80] = [ZGrab2(["http", "--user-agent", "Mozilla/5.0"], 80, http_version_extractor)]
    scanner_map[8080] = [ZGrab2(["http", "--user-agent", "Mozilla/5.0"], 8080, http_version_extractor)]
    scanner_map[443] = [ZGrab2(["http", "--user-agent", "Mozilla/5.0", "--use-https"], 443, http_version_extractor)]

    # scanner_map[25] = [ZGrab2.with_config(["smtp"], 25, smtp_version_extractor)]
    scanner_map[587] = [ZGrab2(["smtp"], 587, smtp_version_extractor)]
    scanner_map[465] = [ZGrab2(["smtp", "--smtps"], 465, smtp_version_extractor)]

    scanner_map[21] = [ZGrab2(["ftp"], 21, ftp_version_extractor)]

    scanner_map[995] = [ZGrab2(["pop3", "--pop3s"], 995)]

    scanner_map[1521] = [ZGrab2(["oracle"], 1521)]

    scanner_map[1433] = [ZGrab2(["mssql"], 1433, mssql_version_extractor)]

    scanner_map[993] = [ZGrab2(["imap", "--imaps"], 993)]

    scanner_map[5671] = [ZGrab2(["amqp091", "--use-tls"], 5671, rabbitmq_version_extractor)]
    scanner_map[5672] = [ZGrab2(["amqp091"], 5672, rabbitmq_version_extractor)]

    scanner_map[3306] = [MySQLScanner(3306)]

    scanner_map[6379] = [RedisScanner(6379)]

    scanner_map[27017] = [MongoDbScanner(27017)]

    return scanner_map


def setup_logging():
    """
    Sets up logging to both console and a daily log file.
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    os.makedirs("logs", exist_ok=True)
    log_path = Path("logs/log.txt")
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    root.addHandler(file_handler)

def setup_cleanup():
    def cleanup_child_processes():
        logger.info("Cleaning up child processes...")
        with CHILD_PROCESSES_LOCK:
            for proc in CHILD_PROCESSES:
                if proc.poll() is None:
                    logger.info(f"Terminating process PID={proc.pid}")
                    proc.terminate()
            for proc in CHILD_PROCESSES:
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process PID={proc.pid} did not exit, killing now")
                    proc.kill()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, exiting...")
        cleanup_child_processes()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)

def parse_args():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Scan services based on IPs from ASN or custom IP list."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--asn",
        type=validate_asn,
        help="ASN to look up (example: AS12345)"
    )
    group.add_argument(
        "--custom-ips",
        type=str,
        help="Path to a file containing IP addresses to scan (example: ips.txt)"
    )

    return parser.parse_args()


async def main():
    """
    Main entry point of the script.
    """
    setup_logging()
    setup_cleanup()

    args = parse_args()

    scanner_map = build_scanner_map()

    if args.asn:
        asn_lookup = CachedAsnLookup(HackerTargetAPI())
        try:
            ip_prefixes_path = await asn_lookup.lookup_asn(args.asn)
        except Exception as e:
            logger.error(f"Failed to lookup ASN: {e}")
            return
    else:
        ip_prefixes_path = args.custom_ips

    logger.info(f"Using IP list from: {ip_prefixes_path}")

    for (port, scanners) in scanner_map.items():
        logger.info(f"Working on {port}")

        zmap = Zmap()
        zmap_output = zmap.scan_ip_prefixes(ip_prefixes_path, port)

        for scanner in scanners:
            scanner.scan_versions(zmap_output)

    # Product version EOL and CVE check
    cache_dir = Path('./cache/version-scanner')
    version_files = list(cache_dir.rglob(f"{args.asn}-*.json"))

    eol_success = Path('./cache/eol/success')
    eol_failure = Path('./cache/eol/failure')

    eol_success.mkdir(parents=True, exist_ok=True)
    eol_failure.mkdir(parents=True, exist_ok=True)

    for file_path in version_files:
        filename = file_path.name
        logger.info(f"Processing {filename} for EOL")
        eol_checker.process_file(file_path, eol_success / filename, eol_failure / filename)

    results_dir = Path('./results')
    results_dir.mkdir(parents=True, exist_ok=True)

    eol_success_files = list(eol_success.rglob(f"{args.asn}-*.json"))
    for eol_file in eol_success_files:
        cve_finder.process_file(eol_file, results_dir / eol_file.name)

    # TLS version check
    tls_version_files = []
    ports = ["993", "995", "443", "465"]

    for port in ports:
        pattern = f"{args.asn}-{port}.txt"
        found = list(cache_dir.rglob(pattern))
        tls_version_files.extend(found)

    tls_results_dir = results_dir / "tls"
    tls_results_dir.mkdir(parents=True, exist_ok=True)

    for file_path in tls_version_files:
        filename = file_path.name
        logger.info(f"Processing {filename} for TLS")
        tls_checker.process_file(file_path, tls_results_dir / filename.replace(".txt", "-tls.json"))


if __name__ == "__main__":
    asyncio.run(main())
