import os
import json
import ipaddress
import matplotlib.pyplot as plt
from collections import defaultdict

def count_total_ips_from_as_directories(base_path, folder_names):
    total_ips = 0
    for folder_name in folder_names:
        folder_path = os.path.join(base_path, folder_name)
        for filename in os.listdir(folder_path):
            if filename.startswith("IP") and filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, "r") as f:
                        for line in f:
                            ip_range = line.strip()
                            if ip_range:
                                try:
                                    network = ipaddress.ip_network(ip_range, strict=False)
                                    total_ips += network.num_addresses
                                except ValueError as e:
                                    print(f"Invalid IP range {ip_range}: {e}")
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")
    return total_ips

def count_responded_and_eol_ips(combined_file_path):
    responded_ips = set()
    eol_ips = 0
    try:
        with open(combined_file_path, "r") as f:
            data = json.load(f)
            for entry in data:
                ip = entry.get("ip")
                if ip:
                    responded_ips.add(ip)
                if entry.get("is_eol", False):
                    eol_ips += 1
    except Exception as e:
        print(f"Failed to read {combined_file_path}: {e}")
    return len(responded_ips), eol_ips

def create_pie_chart(total_ips, responded_ips, eol_ips):
    non_responded_ips = total_ips - responded_ips
    responded_non_eol = responded_ips - eol_ips

    sizes = [non_responded_ips, responded_non_eol, eol_ips]
    labels = ["Non-Responded IPs", "Responded (Non-EOL)", "Responded (EOL)"]
    colors = ["lightgray", "skyblue", "salmon"]

    plt.figure(figsize=(8, 8))
    plt.pie(
        sizes,
        labels=labels,
        autopct=lambda p: f"{p:.1f}%\n({int(p * total_ips / 100)})",
        colors=colors,
        startangle=140,
    )
    plt.title("IP Response Distribution")
    plt.tight_layout()
    plt.show()

# Main script
base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
folder_names = ["AS15625", "AS15916"]  # Replace with actual folder names
combined_file_path = os.path.join(base_path, "business", "combined_server_eol_success.json")

# Count total IPs
total_ips = count_total_ips_from_as_directories(base_path, folder_names)

# Count responded and EOL IPs
responded_ips, eol_ips = count_responded_and_eol_ips(combined_file_path)

# Create pie chart
create_pie_chart(total_ips, responded_ips, eol_ips)