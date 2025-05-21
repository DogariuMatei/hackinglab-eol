import csv
import json
import pymongo


def get_mongodb_version(ip, port=27017, timeout=2):
    try:
        client = pymongo.MongoClient(f"mongodb://{ip}:{port}/",
                                     serverSelectionTimeoutMS=timeout * 1000)
        version = client.server_info().get('version', 'Unknown')
        client.close()
        return version
    except Exception as e:
        return f"Error: {str(e)}"


results = []
with open('output_AS20857_mongodb.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ip = row[0]
        version = get_mongodb_version(ip)

        entry = {
            "ip": ip,
            "version": version
        }

        results.append(entry)
        print(f"Checked {ip}: {version}")


output_filename = "mongodb_versions.json"
with open(output_filename, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"\nResults saved to {output_filename}")