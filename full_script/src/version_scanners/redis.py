import logging
import os
from pathlib import Path

from .base import VersionScanner
import json
import re
import redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class RedisScanner(VersionScanner):

    def __init__(self, port: int):
        self.cache_dir = "./cache/version-scanner/redis"
        self.timeout = 3
        self.port = port

    def scan_versions(self, ips_file: str) -> str:
        os.makedirs(self.cache_dir, exist_ok=True)

        file_stem = Path(ips_file).stem
        save_path = os.path.join(self.cache_dir, f"{file_stem}.json")

        if os.path.exists(save_path):
            logger.info("Using cached Redis scanner output")
            return save_path

        extracted_pairs = []

        with open(ips_file, "r") as f:
            for line in f:
                ip = line.strip()
                if ip is not None:
                    version = self.get_redis_version(ip)

                    if version and re.match(r'^\d+\.\d+(\.\d+)?$', version):
                        server_str = f"Redis/{version}"
                    else:
                        server_str = "Redis"

                    extracted_pairs.append((ip, server_str))

        dicts = [{"ip": ip, "server": version} for ip, version in extracted_pairs]

        try:
            with open(save_path, 'w', encoding='utf-8') as out_file:
                json.dump(dicts, out_file, indent=4)
            logger.info(f"Saved {len(dicts)} extracted entries to {save_path}")
        except Exception as e:
            logger.error(f"Failed to write extracted results to file: {e}")
        return save_path

    def get_redis_version(self, ip):
        try:
            r = redis.Redis(host=ip, port=self.port, socket_timeout=self.timeout, socket_connect_timeout=self.timeout)
            info = r.info()
            version = info.get('redis_version', None)
            r.close()
            if version:
                return str(version)
            else:
                return None
        except (ConnectionError, TimeoutError):
            return None
        except Exception:
            return None
