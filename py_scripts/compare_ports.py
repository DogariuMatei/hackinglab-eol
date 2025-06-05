import os
import json
from collections import defaultdict, Counter
from itertools import combinations
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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

def analyze_top_port_combinations(folder_path, top_n=10):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)
    single_port_counter = Counter()

    # Read JSON files and collect vulnerable ports for each IP
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
                    single_port_counter[port_identifier] += 1
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    # Print the most common single ports
    print(f"\nTop {top_n} most common single ports:")
    for port, count in single_port_counter.most_common(top_n):
        print(f"Port {port}: {count}")

    # Analyze top combinations for each group size
    max_ports = max(len(ports) for ports in ip_vulnerable_ports.values())
    for group_size in range(1, min(max_ports + 1, 7)):  # Limit to 6 as per the requirement
        combination_counter = Counter()

        for ports in ip_vulnerable_ports.values():
            if len(ports) == group_size:  # Only consider IPs with exactly `group_size` ports
                for combo in combinations(sorted(ports), group_size):
                    combination_counter[combo] += 1

        # Get the top N combinations
        print(f"\nTop {top_n} most common port combinations for group size {group_size}:")
        for combo, count in combination_counter.most_common(top_n):
            print(f"{combo}: {count}")

def visualize_port_combinations_heatmap(folder_path, top_n=10):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)

    # Read JSON files and collect vulnerable ports for each IP
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

    # Analyze top combinations for each group size
    max_ports = max(len(ports) for ports in ip_vulnerable_ports.values())
    for group_size in range(2, min(max_ports + 1, 7)):  # Limit to 6 as per the requirement
        combination_counter = Counter()

        for ports in ip_vulnerable_ports.values():
            if len(ports) == group_size:  # Only consider IPs with exactly `group_size` ports
                for combo in combinations(sorted(ports), group_size):
                    combination_counter[combo] += 1

        # Prepare data for heatmap
        if group_size == 2:  # Heatmap is most effective for 2-port combinations
            heatmap_data = defaultdict(lambda: defaultdict(int))
            for (port1, port2), count in combination_counter.items():
                heatmap_data[port1][port2] = count

            # Convert to DataFrame
            df = pd.DataFrame(heatmap_data).fillna(0)

            # Apply logarithmic transformation
            log_df = np.log1p(df)  # log(1 + x) to handle zeros

            # Plot heatmap
            plt.figure(figsize=(12, 8))
            sns.heatmap(log_df, annot=df, fmt=".0f", cmap="YlGnBu", cbar=True)
            plt.title(f"Heatmap of 2-Port Combinations (Group Size {group_size}) with Logarithmic Scale")
            plt.xlabel("Port 1")
            plt.ylabel("Port 2")
            plt.tight_layout()
            plt.show()

def plot_eol_ports_by_server_type(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    server_type_counter = Counter()

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    server_type = entry.get("server", "Unknown")
                    server_type_counter[server_type] += 1
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    # Plot stacked bar chart
    server_types = list(server_type_counter.keys())
    counts = list(server_type_counter.values())

    plt.figure(figsize=(12, 6))
    plt.bar(server_types, counts, color='orange', edgecolor='black')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Server Type")
    plt.ylabel("Number of EOL Ports")
    plt.title("EOL Ports by Server Type")
    plt.tight_layout()
    plt.show()

def plot_eol_ports_by_server_type1(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    server_type_counter = Counter()

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    server_type = entry.get("server", "Unknown")
                    server_type_counter[server_type] += 1
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    # Define custom bins
    bins = [0, 100, 500, 1000, 2000, 8000]
    bin_labels = ["0-100", "100-500", "500-1000", "1000-2000", "2000-8000"]

    # Bin the server counts
    server_counts = list(server_type_counter.values())
    binned_counts = pd.cut(server_counts, bins=bins, labels=bin_labels, right=True)

    # Aggregate counts for each bin
    bin_totals = Counter()
    for bin_label, count in zip(binned_counts, server_counts):
        bin_totals[bin_label] += count

    # Prepare data for plotting
    x = list(bin_totals.keys())
    y = list(bin_totals.values())

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.bar(x, y, color='orange', edgecolor='black')
    plt.xlabel("Number of EOL Ports (Binned)")
    plt.ylabel("Number of Servers")
    plt.title("EOL Ports by Server Type (Binned)")
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    folder = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data"
    #analyze_eol_from_files(folder)
    #analyze_top_port_combinations(folder, top_n=10)
    #visualize_port_combinations_heatmap(folder, top_n=10)
    #plot_eol_ports_by_server_type(folder)
    plot_eol_ports_by_server_type1(folder)


