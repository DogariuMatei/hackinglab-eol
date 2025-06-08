import os
import json
import csv

def combine_clean_versions(konstantin_path, filip_paths, output_path):
    os.makedirs(output_path, exist_ok=True)

    for filename in os.listdir(konstantin_path):
        if filename.startswith("parsed_") and filename.endswith(".json"):
            port = filename.split("_")[1].split(".")[0]
            konstantin_file = os.path.join(konstantin_path, filename)
            output_file = os.path.join(output_path, f"combined_clean_versions_{port}.json")

            combined_data = []

            # Read Konstantin's file
            try:
                with open(konstantin_file, "r", encoding="utf-8") as f:
                    konstantin_data = json.load(f)
                    combined_data.extend(konstantin_data)
            except Exception as e:
                print(f"Error reading {konstantin_file}: {e}")

            # Read Filip's files
            for filip_path in filip_paths:
                filip_file = os.path.join(filip_path, port, "clean_versions.json")
                try:
                    if os.path.isfile(filip_file):
                        with open(filip_file, "r", encoding="utf-8") as f:
                            filip_data = json.load(f)
                            combined_data.extend(filip_data)
                except Exception as e:
                    print(f"Error reading {filip_file}: {e}")

            # Write combined data
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(combined_data, f, indent=4)
                print(f"Combined clean_versions written to {output_file}")
            except Exception as e:
                print(f"Error writing {output_file}: {e}")

def combine_zmap_files(konstantin_path, filip_paths, output_path):
    os.makedirs(output_path, exist_ok=True)

    for filename in os.listdir(konstantin_path):
        if filename.startswith("zmap_") and filename.endswith(".csv"):
            port = filename.split("_")[1].split(".")[0]
            konstantin_file = os.path.join(konstantin_path, filename)
            output_file = os.path.join(output_path, f"combined_zmap_{port}.csv")

            combined_data = []

            # Read Konstantin's file
            try:
                with open(konstantin_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    combined_data.extend(list(reader))
            except Exception as e:
                print(f"Error reading {konstantin_file}: {e}")

            # Read Filip's files
            for filip_path in filip_paths:
                filip_file = os.path.join(filip_path, port, f"zmap_output.csv")
                try:
                    if os.path.isfile(filip_file):
                        with open(filip_file, "r", newline="", encoding="utf-8") as f:
                            reader = csv.reader(f)
                            combined_data.extend(list(reader))
                except Exception as e:
                    print(f"Error reading {filip_file}: {e}")

            # Write combined data
            try:
                with open(output_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerows(combined_data)
                print(f"Combined zmap written to {output_file}")
            except Exception as e:
                print(f"Error writing {output_file}: {e}")


import os
import shutil


def transfer_and_rename_csv_files(source_path, destination_base_path):
    # Ensure the destination base path exists
    os.makedirs(destination_base_path, exist_ok=True)

    # Iterate through files in the source path
    for file_name in os.listdir(source_path):
        if file_name.startswith("zmap_") and file_name.endswith(".csv"):
            # Extract the port number from the file name
            port = file_name.split("_")[-1].split(".")[0]

            # Define the destination folder for the port
            destination_folder = os.path.join(destination_base_path, port)
            os.makedirs(destination_folder, exist_ok=True)

            # Define the new file name and path
            new_file_name = f"zmap_outputAS20857.csv"
            destination_file_path = os.path.join(destination_folder, new_file_name)

            # Move and rename the file
            source_file_path = os.path.join(source_path, file_name)
            shutil.copy(source_file_path, destination_file_path)
            print(f"Moved and renamed: {source_file_path} -> {destination_file_path}")




if __name__ == "__main__":
    # Paths
    konstantin_clean_versions = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data\clean_versions"
    konstantin_zmap = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data\zmap"
    filip_paths = [
        r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS57043",
        r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS29063"
    ]
    output_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\combined_data_Filip_Konstantin_Hosting"

    # Combine clean_versions
    combine_clean_versions(konstantin_clean_versions, filip_paths, output_path)
    #
    # # Combine zmap files
    combine_zmap_files(konstantin_zmap, filip_paths, output_path)

    # Example usage
    # source_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data\zmap"
    # destination_base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS20857"
    # transfer_and_rename_csv_files(source_path, destination_base_path)