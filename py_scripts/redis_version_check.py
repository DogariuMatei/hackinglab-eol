import csv
import json
import redis
from redis.exceptions import ConnectionError, TimeoutError


def get_redis_version(ip, port=6379, timeout=3):
    try:
        r = redis.Redis(host=ip, port=port, socket_timeout=timeout, socket_connect_timeout=timeout)
        info = r.info()
        version = info.get('redis_version', 'Unknown')
        r.close()
        return version
    except (ConnectionError, TimeoutError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


# Read IPs from CSV and collect results
results = []
with open('output_AS20857_redis.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ip = row[0]  # Assuming IP is in the first column
        version = get_redis_version(ip)

        # Create entry in the requested format
        entry = {
            "ip": ip,
            "version": f"Redis {version}"
        }

        results.append(entry)
        print(f"Checked {ip}: Redis {version}")

# Save results to JSON file
output_filename = "redis_versions_AS20857.json"
with open(output_filename, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"\nResults saved to {output_filename}")