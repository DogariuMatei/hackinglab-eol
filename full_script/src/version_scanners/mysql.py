import logging
import os
from pathlib import Path

from .base import VersionScanner
import json
import re
import socket
import mysql.connector

logger = logging.getLogger(__name__)

class MySQLScanner(VersionScanner):

    def __init__(self, port: int):
        self.cache_dir = "./cache/version-scanner/mysql"
        self.timeout = 3
        self.port = port

    def scan_versions(self, ips_file: str) -> str:
        os.makedirs(self.cache_dir, exist_ok=True)

        file_stem = Path(ips_file).stem
        save_path = os.path.join(self.cache_dir, f"{file_stem}.json")

        if os.path.exists(save_path):
            logger.info("Using cached MySQL scanner output")
            return save_path

        extracted_pairs = []

        with open(ips_file, "r") as f:
            for line in f:
                ip = line.strip()
                if ip is not None:
                    product, version = self.get_mysql_or_mariadb_version(ip)

                    if product and version:
                        server_val = f"{product}/{version}"
                    elif product:
                        server_val = product
                    else:
                        continue

                    extracted_pairs.append((ip, server_val))

        dicts = [{"ip": ip, "server": version} for ip, version in extracted_pairs]

        try:
            with open(save_path, 'w', encoding='utf-8') as out_file:
                json.dump(dicts, out_file, indent=4)
            logger.info(f"Saved {len(dicts)} extracted entries to {save_path}")
        except Exception as e:
            logger.error(f"Failed to write extracted results to file: {e}")
        return save_path

    def extract_mariadb_version(self, version_string):
        mariadb_match = re.search(r'5\.5\.5-(\d+\.\d+\.\d+)', version_string)
        if mariadb_match:
            return mariadb_match.group(1)
        mariadb_match = re.search(r'(\d+\.\d+\.\d+)-MariaDB', version_string)
        if mariadb_match:
            return mariadb_match.group(1)
        return None

    def extract_mysql_version(self, version_string):
        mysql_match = re.search(r'(\d+\.\d+\.\d+)', version_string)
        if mysql_match:
            return mysql_match.group(1)
        return None

    def get_mysql_or_mariadb_version(self, ip: str):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect((ip, self.port))
            data = s.recv(4096)
            s.close()
            data_str = data.decode('utf-8', errors='ignore')

            if "MariaDB" in data_str:
                version = self.extract_mariadb_version(data_str)
                return ("MariaDB", version) if version else ("MariaDB", None)
            if len(data) > 5:
                pos = 5
                version_end = data.find(b'\0', pos)
                if version_end > pos:
                    full_version = data[pos:version_end].decode('utf-8', errors='ignore')
                    version = self.extract_mysql_version(full_version)
                    return ("MySQL", version) if version else ("MySQL", None)
        except Exception:
            pass

        try:
            connection = mysql.connector.connect(
                host=ip,
                port=self.port,
                user="root",
                password="",
                connection_timeout=self.timeout
            )
            if connection.is_connected():
                cursor = connection.cursor()
                cursor.execute("SELECT VERSION();")
                full_version = cursor.fetchone()[0]
                cursor.close()
                connection.close()

                if "MariaDB" in full_version:
                    version = self.extract_mariadb_version(full_version)
                    return ("MariaDB", version) if version else ("MariaDB", None)
                else:
                    version = self.extract_mysql_version(full_version)
                    return ("MySQL", version) if version else ("MySQL", None)
        except Exception:
            pass

        return (None, None)
