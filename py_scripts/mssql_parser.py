import json
import re

input_filename = "AAS20857/zgrab_results/AS20857_1433_results_27may.json"
output_filename = "AAS20857/clean_version_ip/mssql_versions_AS20857_3june.json"

results = []

with open(input_filename, 'r') as infile:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            ip = entry.get("ip")
            data = entry.get("data", {}).get("mssql", {})
            status = data.get("status")
            result = data.get("result", {})
            version = result.get("version")

            if status == "success" and version and re.match(r'^\d+(\.\d+)+$', version):
                server_val = f"MSSQL/{version}"
                results.append({
                    "ip": ip,
                    "server": server_val
                })
                print(f"Checked {ip}: {server_val}")
        except Exception as e:
            print(f"Error processing line: {line}\n{e}")

with open(output_filename, 'w') as outfile:
    json.dump(results, outfile, indent=2)

print(f"\nResults saved to {output_filename}")