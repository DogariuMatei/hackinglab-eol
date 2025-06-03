import csv
import json
import redis
import re
from redis.exceptions import ConnectionError, TimeoutError

def get_redis_version(ip, port=6379, timeout=3):
    try:
        r = redis.Redis(host=ip, port=port, socket_timeout=timeout, socket_connect_timeout=timeout)
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

results = []
with open('AAS20857/zmap_output/output_AS20857_redis.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ip = row[0]
        version = get_redis_version(ip)

        if version and re.match(r'^\d+\.\d+(\.\d+)?$', version):
            server_str = f"Redis/{version}"
        else:
            server_str = "Redis"

        entry = {
            "ip": ip,
            "server": server_str
        }

        results.append(entry)
        print(f"Checked {ip}: {server_str}")

output_filename = "AAS20857/clean_version_ip/redis_versions_AS20857_3june.json"
with open(output_filename, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"\nResults saved to {output_filename}")