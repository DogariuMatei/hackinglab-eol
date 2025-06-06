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

def combine_and_analyze_eol_from_files(folder_path1, folder_path2):
    if not os.path.isdir(folder_path1) or not os.path.isdir(folder_path2):
        raise ValueError("One or both folder paths are not valid.")

    ip_vulnerable_ports = defaultdict(set)

    # Combine data from both folders
    for folder_path in [folder_path1, folder_path2]:
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
    bars = plt.bar(x, y, color='salmon', edgecolor='black')

    # Add total number on top of each bar
    for bar, count in zip(bars, y):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 str(count), ha='center', va='bottom', fontsize=10)

    plt.xlabel("Number of Vulnerable Ports")
    plt.ylabel("Number of IPs")
    plt.title("IP Vulnerability Count across Ports (Combined)")
    plt.xticks(x)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def combine_and_analyze_top_port_combinations(folder_path1, folder_path2, top_n=10):
    if not os.path.isdir(folder_path1) or not os.path.isdir(folder_path2):
        raise ValueError("One or both folder paths are not valid.")

    ip_vulnerable_ports = defaultdict(set)
    single_port_counter = Counter()

    # Combine data from both folders
    for folder_path in [folder_path1, folder_path2]:
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
            if len(ports) >= group_size:  # Consider IPs with at least `group_size` ports
                for combo in combinations(sorted(ports), group_size):
                    combination_counter[combo] += 1

        # Get the top N combinations
        print(f"\nTop {top_n} most common port combinations for group size {group_size}:")
        for combo, count in combination_counter.most_common(top_n):
            print(f"{combo}: {count}")

def combine_and_visualize_port_combinations_heatmap(folder_path1, folder_path2, top_n=10):
    if not os.path.isdir(folder_path1) or not os.path.isdir(folder_path2):
        raise ValueError("One or both folder paths are not valid.")

    ip_vulnerable_ports = defaultdict(set)

    # Combine data from both folders
    for folder_path in [folder_path1, folder_path2]:
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
            plt.title(f"Heatmap of 2-Port Combinations (Combined) with Logarithmic Scale")
            plt.xlabel("Port 1")
            plt.ylabel("Port 2")
            plt.tight_layout()
            plt.show()

def plot_eol_ports_by_server_type_combined(folder_path1, folder_path2):
    if not os.path.isdir(folder_path1) or not os.path.isdir(folder_path2):
        raise ValueError("One or both folder paths are not valid.")

    server_type_counter = Counter()

    # Process files from both folders
    for folder_path in [folder_path1, folder_path2]:
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
    plt.title("EOL Ports by Server Type (Combined)")
    plt.tight_layout()
    plt.show()

def create_multi_level_sankey(folder_paths):
    ip_vulnerable_ports = defaultdict(set)

    # Combine data from multiple folders
    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            raise ValueError(f"{folder_path} is not a valid folder.")
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

def create_port_cooccurrence_graph(folder_paths, min_weight=20):
    ip_vulnerable_ports = defaultdict(set)

    # Combine data from multiple folders
    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            raise ValueError(f"{folder_path} is not a valid folder.")
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


if __name__ == "__main__":
    folder1 = r""
    folder2 = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\combined_data"

    combine_and_analyze_eol_from_files(folder1, folder2)
    combine_and_analyze_top_port_combinations(folder1, folder2, top_n=10)
    combine_and_visualize_port_combinations_heatmap(folder1, folder2, top_n=10)
    plot_eol_ports_by_server_type_combined(folder1, folder2)
    create_multi_level_sankey([folder1, folder2])
    create_port_cooccurrence_graph([folder1, folder2], min_weight=50)




