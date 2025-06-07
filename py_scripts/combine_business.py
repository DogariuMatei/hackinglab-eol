import os
import json

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

import ipaddress

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

# Example usage
base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
folder_names = ["AS15625ING", "AS15916"]  # Replace with actual folder names
#combine_server_eol_files(base_path, folder_names)
path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS1101\IPAS1101.txt"
print(calculate_total_ips_from_file(path))