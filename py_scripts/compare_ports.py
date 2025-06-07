import os
import json
from collections import defaultdict, Counter
from itertools import combinations
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import networkx as nx

def analyze_eol_from_files(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        port_identifier = os.path.splitext(filename)[0]

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    ip = entry.get("ip")
                    ip_vulnerable_ports[ip].add(port_identifier)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    vuln_count_distribution = Counter(len(ports) for ports in ip_vulnerable_ports.values())

    x = sorted(vuln_count_distribution)
    y = [vuln_count_distribution[i] for i in x]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(x, y, color='#8c96c6', edgecolor='black')

    for bar, count in zip(bars, y):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 str(count), ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.xlabel("Number of Vulnerable Ports", fontsize=14, fontweight='bold')
    plt.ylabel("Number of IPs", fontsize=14, fontweight='bold')
    plt.title("IP Vulnerability Count across Ports", fontsize=16, fontweight='bold')
    plt.xticks(x, fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def analyze_top_port_combinations(folder_path, top_n=10):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)
    single_port_counter = Counter()

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        port_identifier = os.path.splitext(filename)[0]

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

    print(f"\nTop {top_n} most common single ports:")
    for port, count in single_port_counter.most_common(top_n):
        print(f"Port {port}: {count}")

    max_ports = max(len(ports) for ports in ip_vulnerable_ports.values())

    for group_size in range(1, min(max_ports + 1, 7)):
        combination_counter = Counter()

        for ports in ip_vulnerable_ports.values():
            if len(ports) == group_size:
                key = tuple(sorted(ports))
                combination_counter[key] += 1

        print(f"\nTop {top_n} most common exact port sets for group size {group_size}:")
        for combo, count in combination_counter.most_common(top_n):
            print(f"{combo}: {count}")

def plot_eol_ports_by_server_type_with_percentage(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    eol_server_type_counter = Counter()
    total_server_type_counter = Counter()

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                server_type = entry.get("server", "Unknown")
                if server_type.lower() == "openssl":
                    continue
                total_server_type_counter[server_type] += 1
                if entry.get("is_eol"):
                    eol_server_type_counter[server_type] += 1
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    server_types = list(eol_server_type_counter.keys())
    eol_counts = [eol_server_type_counter[server_type] for server_type in server_types]
    total_counts = [total_server_type_counter[server_type] for server_type in server_types]
    percentages = [
        (eol / total * 100) if total > 0 else 0
        for eol, total in zip(eol_counts, total_counts)
    ]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(server_types, eol_counts, color='#8856a7', edgecolor='black')

    for bar, percentage in zip(bars, percentages):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{percentage:.1f}%",
            ha='center',
            va='bottom',
            fontsize=12,
            fontweight='bold'
        )

    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.xlabel("Server Type", fontsize=14, fontweight='bold')
    plt.ylabel("Number of EOL Ports", fontsize=14, fontweight='bold')
    plt.title("EOL Ports by Server Type with Percentage of Total Versions", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()

def visualize_total_port_cooccurrence_heatmap(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        port_identifier = os.path.splitext(filename)[0]

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    ip = entry.get("ip")
                    ip_vulnerable_ports[ip].add(port_identifier)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    cooccurrence_counter = Counter()

    for ports in ip_vulnerable_ports.values():
        for port1, port2 in combinations(sorted(ports), 2):
            cooccurrence_counter[(port1, port2)] += 1
            cooccurrence_counter[(port2, port1)] += 1

    heatmap_data = defaultdict(lambda: defaultdict(int))
    for (p1, p2), count in cooccurrence_counter.items():
        heatmap_data[p1][p2] = count

    df = pd.DataFrame(heatmap_data).fillna(0)

    all_ports = sorted(df.index.union(df.columns))
    df = df.reindex(index=all_ports, columns=all_ports, fill_value=0)

    log_df = np.log1p(df)

    plt.figure(figsize=(12, 8))
    sns.heatmap(log_df, annot=df, fmt=".0f", cmap="Purples", cbar=True, annot_kws={"size": 10})
    plt.title("Total Port Pair Co-Occurrence (Log Scale)", fontsize=16, fontweight='bold')
    plt.xlabel("Port", fontsize=14, fontweight='bold')
    plt.ylabel("Port", fontsize=14, fontweight='bold')
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\combined_data"
    #
    analyze_eol_from_files(folder)
    analyze_top_port_combinations(folder, top_n=10)
    visualize_total_port_cooccurrence_heatmap(folder)
    plot_eol_ports_by_server_type_with_percentage(folder)





def visualize_port_combinations_heatmap(folder_path, top_n=10):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    ip_vulnerable_ports = defaultdict(set)

    # Read data from the folder
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

    max_ports = max(len(ports) for ports in ip_vulnerable_ports.values())
    for group_size in range(2, min(max_ports + 1, 7)):  # Limit to 6 as per the requirement
        combination_counter = Counter()

        for ports in ip_vulnerable_ports.values():
            if len(ports) >= group_size:  # Consider IPs with at least `group_size` ports
                for combo in combinations(sorted(ports), group_size):
                    combination_counter[combo] += 1

        if group_size == 2:  # Heatmap is most effective for 2-port combinations
            heatmap_data = defaultdict(lambda: defaultdict(int))
            for (port1, port2), count in combination_counter.items():
                heatmap_data[port1][port2] = count
                heatmap_data[port2][port1] = count  # Ensure symmetry

            # Convert to DataFrame
            df = pd.DataFrame(heatmap_data).fillna(0)

            # Ensure symmetry by reindexing rows and columns in the same order
            all_ports = sorted(df.index.union(df.columns))
            df = df.reindex(index=all_ports, columns=all_ports, fill_value=0)

            # Apply logarithmic transformation
            log_df = np.log1p(df)  # log(1 + x) to handle zeros

            # Plot heatmap
            plt.figure(figsize=(12, 8))
            sns.heatmap(log_df, annot=df, fmt=".0f", cmap="YlGnBu", cbar=True)
            plt.title(f"Heatmap of 2-Port Combinations with Logarithmic Scale")
            plt.xlabel("Port 1")
            plt.ylabel("Port 2")
            plt.tight_layout()
            plt.show()

def plot_eol_ports_by_server_type(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"{folder_path} is not a valid folder.")

    server_type_counter = Counter()

    # Read data from the folder
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

def create_multi_level_sankey(folder_path):
    ip_vulnerable_ports = defaultdict(set)

    # Read data from the folder
    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        port_identifier = os.path.splitext(filename)[0]  # Remove ".json"

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    ip = entry.get("ip")
                    ip_vulnerable_ports[ip].add(port_identifier)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    # Prepare data for the Sankey diagram
    max_ports = max(len(ports) for ports in ip_vulnerable_ports.values())
    combination_counters = [Counter() for _ in range(max_ports)]

    for ports in ip_vulnerable_ports.values():
        for group_size in range(1, len(ports) + 1):
            for combo in combinations(sorted(ports), group_size):
                combination_counters[group_size - 1][combo] += 1

    # Filter out combinations with fewer than 20 occurrences
    combination_counters = [
        {combo: count for combo, count in counter.items() if count >= 20}
        for counter in combination_counters
    ]

    # Create nodes and links
    nodes = []
    node_indices = {}
    sources = []
    targets = []
    values = []

    for level, counter in enumerate(combination_counters):
        for combo, count in counter.items():
            combo_str = ", ".join(combo)
            if combo_str not in node_indices:
                node_indices[combo_str] = len(nodes)
                nodes.append(combo_str)

            # Link to larger combinations in the next level
            if level < len(combination_counters) - 1:
                for next_combo, next_count in combination_counters[level + 1].items():
                    if set(combo).issubset(next_combo):
                        next_combo_str = ", ".join(next_combo)
                        if next_combo_str not in node_indices:
                            node_indices[next_combo_str] = len(nodes)
                            nodes.append(next_combo_str)

                        sources.append(node_indices[combo_str])
                        targets.append(node_indices[next_combo_str])
                        values.append(next_count)

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        )
    )])

    fig.update_layout(title_text="Multi-Level Sankey Diagram: Port Combinations", font_size=10)
    fig.show()

def create_port_cooccurrence_graph(folder_path, min_weight=20):
    ip_vulnerable_ports = defaultdict(set)

    # Read data from the folder
    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)
        port_identifier = os.path.splitext(filename)[0]  # Remove ".json"

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            for entry in data:
                if entry.get("is_eol"):
                    ip = entry.get("ip")
                    ip_vulnerable_ports[ip].add(port_identifier)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    # Count co-occurrences of ports
    cooccurrence_counter = Counter()
    for ports in ip_vulnerable_ports.values():
        for port1, port2 in combinations(sorted(ports), 2):
            cooccurrence_counter[(port1, port2)] += 1

    # Create a graph
    G = nx.Graph()
    for (port1, port2), weight in cooccurrence_counter.items():
        if weight >= min_weight:  # Filter edges by minimum weight
            G.add_edge(port1, port2, weight=weight)

    # Draw the graph
    pos = nx.spring_layout(G, seed=42)  # Layout for consistent visualization
    plt.figure(figsize=(12, 8))

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color="skyblue")

    # Draw edges with thickness proportional to weight
    edges = G.edges(data=True)
    nx.draw_networkx_edges(
        G, pos,
        edgelist=[(u, v) for u, v, d in edges],
        width=[d["weight"] / 10 for u, v, d in edges],  # Scale edge thickness
        alpha=0.7
    )

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_color="black")

    plt.title("Network Graph: Port Co-occurrence")
    plt.tight_layout()
    plt.show()

