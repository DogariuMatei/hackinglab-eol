import os
import json
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

def analyze_eol_from_files(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        port_identifier = os.path.splitext(filename)[0]  # remove ".json"

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    ip = entry.get("ip")
                    ip_vulnerable_ports[ip].add(port_identifier)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    # Count how many ports each IP is vulnerable on
    vuln_count_distribution = Counter(len(ports) for ports in ip_vulnerable_ports.values())

    # Plotting
    x = sorted(vuln_count_distribution)
    y = [vuln_count_distribution[i] for i in x]

    plt.figure(figsize=(10, 6))
    plt.bar(x, y, color='salmon', edgecolor='black')
    plt.xlabel("Number of Vulnerable Ports")
    plt.ylabel("Number of IPs")
    plt.title("IP Vulnerability Count across Ports")
    plt.xticks(x)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data"
    analyze_eol_from_files(folder)
