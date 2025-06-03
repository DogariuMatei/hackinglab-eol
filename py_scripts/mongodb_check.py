import csv
import json
import pymongo
import re


def get_mongodb_version(ip, port=27017, timeout=2):
    try:
        client = pymongo.MongoClient(f"mongodb://{ip}:{port}/",
                                     serverSelectionTimeoutMS=timeout * 1000)
        version = client.server_info().get('version', None)
        client.close()
        return version
    except Exception:
        return None


results = []
with open('AAS20857/zmap_output/output_AS20857_mongodb.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ip = row[0]
        version = get_mongodb_version(ip)

        # If version is a valid version string: e.g., '4.2.23', else just "MongoDB"
        if version and re.match(r'^\d+\.\d+(\.\d+)?$', str(version)):
            server_str = f"MongoDB/{version}"
        else:
            server_str = "MongoDB"

        entry = {
            "ip": ip,
            "server": server_str
        }

        results.append(entry)
        print(f"Checked {ip}: {server_str}")

output_filename = "AAS20857/clean_version_ip/mongodb_versions_AS20857_june3.json"
with open(output_filename, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"\nResults saved to {output_filename}")