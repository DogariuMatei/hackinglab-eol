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

# Example usage
base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
folder_names = ["AS15625ING", "AS15916ABN"]  # Replace with actual folder names
combine_server_eol_files(base_path, folder_names)