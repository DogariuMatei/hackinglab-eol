import os
import json
import csv
import ipaddress
import matplotlib.pyplot as plt

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

    # Calculate non-responding IPs
    responding_ips_count = len(unique_responding_ips)
    non_responding_ips_count = total_ips_count - responding_ips_count

    # Create a combined pie chart
    labels = ["Responding IPs", "Non-Responding IPs"]
    sizes = [responding_ips_count, non_responding_ips_count]
    colors = ["#4a90e2", "#8856a7"]  # Updated blue color for better contrast
    explode = (0.1, 0)  # Slightly explode the first slice

    plt.figure(figsize=(10, 10))
    plt.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        explode=explode,
        textprops={'fontsize': 14, 'fontweight': 'bold'}
    )
    plt.title("IP Response Distribution of Hosting ASs", fontsize=18, fontweight="bold")
    plt.tight_layout()
    plt.show()


# Example usage
base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
folder_names = ["AS29063", "AS57043", "AS20857"]
#combine_server_eol_files(base_path, folder_names)
create_combined_pie_chart(base_path, folder_names)
# path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS20857\IPAS20857.txt"
# print(calculate_total_ips_from_file(path))