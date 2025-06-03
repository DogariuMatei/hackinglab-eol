import os
import json
from collections import defaultdict, Counter
import matplotlib.pyplot as plt

def analyze_eol(folder_name):
    base_path = os.path.join("data_filip", folder_name)
    if not os.path.isdir(base_path):
        raise ValueError(f"{base_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)

    # Each subfolder corresponds to a port
    for subfolder in os.listdir(base_path):
        print(subfolder)
        subfolder_path = os.path.join(base_path, subfolder)
        if not os.path.isdir(subfolder_path):
            print("Skip1")
            continue

        json_file = os.path.join(subfolder_path, "server_eol_success" + "" + ".json") #folder_name
        if not os.path.isfile(json_file):
            print("Skip2")
            continue

        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    ip = entry.get("ip")
                    ip_vulnerable_ports[ip].add(subfolder)
        except Exception as e:
            print(f"Failed to read {json_file}: {e}")

    # Count how many ports each IP is vulnerable on
    vuln_count_distribution = Counter(len(ports) for ports in ip_vulnerable_ports.values())

    # Plotting
    x = sorted(vuln_count_distribution)
    y = [vuln_count_distribution[i] for i in x]

    plt.figure(figsize=(10, 6))
    plt.bar(x, y, color='skyblue', edgecolor='black')
    plt.xlabel("Number of Vulnerable Ports")
    plt.ylabel("Number of IPs")
    plt.title(f"IP Vulnerability Count across Ports for {folder_name}")
    plt.xticks(x)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else input("Enter folder name (e.g., AS57043): ")
    analyze_eol(folder)
