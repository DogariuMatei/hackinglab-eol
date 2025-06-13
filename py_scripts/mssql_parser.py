import json
import re

def process_file(input_filename, output_filename):
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
