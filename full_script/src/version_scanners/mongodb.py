import logging
import os
from pathlib import Path

from .base import VersionScanner
import json
import re
import pymongo

logger = logging.getLogger(__name__)

class MongoDbScanner(VersionScanner):

    def __init__(self, port: int):
        self.cache_dir = "./cache/version-scanner/mongodb"
        self.timeout = 2
        self.port = port

    def scan_versions(self, ips_file: str) -> str:
        os.makedirs(self.cache_dir, exist_ok=True)

        file_stem = Path(ips_file).stem
        save_path = os.path.join(self.cache_dir, f"{file_stem}.json")

        if os.path.exists(save_path):
            logger.info("Using cached MongoDb scanner output")
            return save_path

        extracted_pairs = []

        with open(ips_file, "r") as f:
            for line in f:
                ip = line.strip()
                if ip is not None:
                    version = self.get_mongodb_version(ip)

                    # If version is a valid version string: e.g., '4.2.23', else just "MongoDB"
                    if version and re.match(r'^\d+\.\d+(\.\d+)?$', str(version)):
                        server_str = f"MongoDB/{version}"
                    else:
                        server_str = "MongoDB"

                    extracted_pairs.append((ip, server_str))

        dicts = [{"ip": ip, "server": version} for ip, version in extracted_pairs]

        try:
            with open(save_path, 'w', encoding='utf-8') as out_file:
                json.dump(dicts, out_file, indent=4)
            logger.info(f"Saved {len(dicts)} extracted entries to {save_path}")
        except Exception as e:
            logger.error(f"Failed to write extracted results to file: {e}")
        return save_path

    def get_mongodb_version(self, ip, port=27017):
        try:
            client = pymongo.MongoClient(f"mongodb://{ip}:{port}/",
                                        serverSelectionTimeoutMS=self.timeout * 1000)
            version = client.server_info().get('version', None)
            client.close()
            return version
        except Exception:
            return None
