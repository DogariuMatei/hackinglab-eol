import os
import json
import csv
import ipaddress
import matplotlib.pyplot as plt
import seaborn as sns

def combine_server_eol_files(base_path, folder_names, output_folder_name="business"):
    # Create the output folder if it doesn't exist
    output_folder = os.path.join(base_path, output_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    combined_data = []

    for folder_name in folder_names:
        folder_path = os.path.join(base_path, folder_name)

        if not os.path.isdir(folder_path):
            print(f"Skipping {folder_path}, not a valid directory.")
            continue

        # Iterate through subfolders (ports)
        for port_folder in os.listdir(folder_path):
            port_folder_path = os.path.join(folder_path, port_folder)

            if not os.path.isdir(port_folder_path):
                continue

            # Look for server_eol_success.json
            json_file_path = os.path.join(port_folder_path, "server_eol_success.json")
            if os.path.isfile(json_file_path):
                try:
                    with open(json_file_path, "r") as f:
                        data = json.load(f)
                        combined_data.extend(data if isinstance(data, list) else [data])
                except Exception as e:
                    print(f"Failed to read {json_file_path}: {e}")

    # Write the combined data to a new file
    output_file_path = os.path.join(output_folder, "combined_server_eol_success.json")
    try:
        with open(output_file_path, "w") as f:
            json.dump(combined_data, f, indent=4)
        print(f"Combined file created at: {output_file_path}")
    except Exception as e:
        print(f"Failed to write combined file: {e}")

def calculate_total_ips_from_file(filepath):
    """
    Reads a text file, calculates the total number of IP addresses from each
    CIDR notation found, and returns the sum.

    Args:
        filepath (str): The path to the text file containing CIDR notations.
                        Each CIDR should be on a new line.

    Returns:
        int: The grand total of IP addresses from all valid CIDR entries in the file.
    """
    total_ips_grand_sum = 0
    line_number = 0
    print(f"Processing file: {filepath}\n")

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line_number += 1
                cidr_notation = line.strip()  # Remove leading/trailing whitespace

                if not cidr_notation:  # Skip empty lines
                    continue

                try:
                    network = ipaddress.ip_network(cidr_notation, strict=False)
                    total_ips_grand_sum += network.num_addresses
                    print(f"  Line {line_number}: '{cidr_notation}' - IPs: {network.num_addresses}")
                except ValueError:
                    print(f"  Line {line_number}: Warning - Invalid CIDR notation '{cidr_notation}'. Skipping.")
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return -1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return -1

    print(f"\n--- Calculation Complete ---")
    print(f"Total IP addresses from all valid CIDR blocks: {total_ips_grand_sum}")
    return total_ips_grand_sum

def create_combined_pie_chart(base_path, folder_names):
    unique_responding_ips = set()
    total_ips_count = 0

    for folder_name in folder_names:
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.isdir(folder_path):
            print(f"Skipping {folder_path}, not a valid directory.")
            continue

        # Collect unique responding IPs from zmap_output<initialFolderName>.csv
        for port_folder in os.listdir(folder_path):
            port_folder_path = os.path.join(folder_path, port_folder)
            if not os.path.isdir(port_folder_path):
                continue

            csv_file_path = os.path.join(port_folder_path, f"zmap_output{folder_name}.csv")
            if os.path.isfile(csv_file_path):
                try:
                    with open(csv_file_path, "r") as f:
                        reader = csv.reader(f)
                        next(reader)  # Skip header
                        for row in reader:
                            if row:  # Ensure the row is not empty
                                unique_responding_ips.add(row[0].strip())
                except Exception as e:
                    print(f"Failed to read {csv_file_path}: {e}")

        # Count total IPs from IP<initialFolderName>.txt
        cidr_file_path = os.path.join(folder_path, f"IP{folder_name}.txt")
        try:
            with open(cidr_file_path, "r") as f:
                for line in f:
                    cidr_notation = line.strip()
                    if not cidr_notation:
                        continue
                    try:
                        network = ipaddress.ip_network(cidr_notation, strict=False)
                        total_ips_count += network.num_addresses
                    except ValueError:
                        print(f"Warning: Invalid CIDR notation '{cidr_notation}'. Skipping.")
        except FileNotFoundError:
            print(f"Error: The file '{cidr_file_path}' was not found.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue

    print(f"Total IPs: {total_ips_count}") # Added print for total_ips_count
    # Calculate non-responding IPs
    responding_ips_count = len(unique_responding_ips)
    non_responding_ips_count = total_ips_count - responding_ips_count

    # Create a combined pie chart
    labels = ["Responding IPs", "Non-Responding IPs"]
    sizes = [responding_ips_count, non_responding_ips_count]
    colors = ["#8c96c6", "#810f7c"]  # Updated blue color for better contrast
    explode = (0.1, 0)  # Slightly explode the first slice

    fig, ax = plt.subplots(figsize=(10, 10))

    # Add wedgeprops for borders and autopct with a custom function for text color
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        explode=explode,
        textprops={'fontsize': 14, 'fontweight': 'bold'},
        wedgeprops={"edgecolor": "black", 'linewidth': 1} # Added border
    )

    # Set the color of the percentage text for the second slice (dark purple) to white
    if len(autotexts) > 1:
        autotexts[1].set_color('white')
        autotexts[0].set_color('white')

    ax.set_title("IP Response Distribution of ISP ASs", fontsize=18, fontweight="bold")
    plt.tight_layout()
    plt.show()


def create_bar_chart(base_path, folder_types):
    data = []  # Store data for each folder type

    for folder_type, folder_names in folder_types.items():
        total_ips_count = 0
        unique_responding_ips = set()

        for folder_name in folder_names:
            folder_path = os.path.join(base_path, folder_name)
            if not os.path.isdir(folder_path):
                print(f"Skipping {folder_path}, not a valid directory.")
                continue

            # Collect unique responding IPs from zmap_output<initialFolderName>.csv
            for port_folder in os.listdir(folder_path):
                port_folder_path = os.path.join(folder_path, port_folder)
                if not os.path.isdir(port_folder_path):
                    continue

                csv_file_path = os.path.join(port_folder_path, f"zmap_output{folder_name}.csv")
                if os.path.isfile(csv_file_path):
                    try:
                        with open(csv_file_path, "r") as f:
                            reader = csv.reader(f)
                            next(reader)  # Skip header
                            for row in reader:
                                if row:  # Ensure the row is not empty
                                    unique_responding_ips.add(row[0].strip())
                    except Exception as e:
                        print(f"Failed to read {csv_file_path}: {e}")

            # Count total IPs from IP<initialFolderName>.txt
            cidr_file_path = os.path.join(folder_path, f"IP{folder_name}.txt")
            try:
                with open(cidr_file_path, "r") as f:
                    for line in f:
                        cidr_notation = line.strip()
                        if not cidr_notation:
                            continue
                        try:
                            network = ipaddress.ip_network(cidr_notation, strict=False)
                            total_ips_count += network.num_addresses
                        except ValueError:
                            print(f"Warning: Invalid CIDR notation '{cidr_notation}'. Skipping.")
            except FileNotFoundError:
                print(f"Error: The file '{cidr_file_path}' was not found.")
                continue
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                continue

        responding_ips_count = len(unique_responding_ips)
        non_responding_ips_count = total_ips_count - responding_ips_count

        # Calculate percentages
        responding_percentage = (responding_ips_count / total_ips_count) * 100 if total_ips_count > 0 else 0
        non_responding_percentage = (non_responding_ips_count / total_ips_count) * 100 if total_ips_count > 0 else 0

        data.append({
            "Type": folder_type,
            "Responding": responding_percentage,
            "Non-Responding": non_responding_percentage
        })

    # Create the bar chart
    plt.figure(figsize=(14, 8))  # Increase figure size
    sns.set_theme(style="whitegrid")
    colors = ["#8c96c6", "#810f7c"]  # Blue-to-dark-purple gradient

    for i, entry in enumerate(data):
        plt.bar(i - 0.2, entry["Responding"], width=0.4, color=colors[0], label="Responding" if i == 0 else "")
        plt.bar(i + 0.2, entry["Non-Responding"], width=0.4, color=colors[1], label="Non-Responding" if i == 0 else "")
        plt.text(i - 0.2, entry["Responding"] + 1, f"{entry['Responding']:.1f}%", ha="center", fontsize=16, fontweight="bold")
        plt.text(i + 0.2, entry["Non-Responding"] + 1, f"{entry['Non-Responding']:.1f}%", ha="center", fontsize=16, fontweight="bold")

    plt.xticks(range(len(data)), [entry["Type"] for entry in data], fontsize=16, fontweight="bold")
    plt.yticks(fontsize=16, fontweight="bold")
    plt.ylabel("Percentage (%)", fontsize=18, fontweight="bold")
    plt.title("Responding vs Non-Responding IPs by AS Type", fontsize=20, fontweight="bold")
    plt.legend(fontsize=16, loc="center right")
    plt.tight_layout()
    plt.show()
# Example usage
# base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
# folder_names = ["AS41960", "AS15670"]
# #combine_server_eol_files(base_path, folder_names)
# create_combined_pie_chart(base_path, folder_names)
# # path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS20857\IPAS20857.txt"
# # print(calculate_total_ips_from_file(path))

base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
folder_types = {
    "Business": ["AS15916", "AS15625"],
    "Education": ["AS1101",],
    "Hosting": ["AS57043", "AS20857", "AS28878"],
    "ISP": ["AS41960", "AS15670"]
}
create_bar_chart(base_path, folder_types)