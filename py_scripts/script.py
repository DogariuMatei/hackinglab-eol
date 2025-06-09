import os
import shutil

def copy_eol_files(source_base_path, destination_base_path):
    # Ensure the destination base path exists
    os.makedirs(destination_base_path, exist_ok=True)

    # Iterate through folders starting with "ASXXXXX"
    for folder_name in os.listdir(source_base_path):
        if folder_name.startswith("AS") and folder_name[2:].isdigit():
            source_folder = os.path.join(source_base_path, folder_name)
            destination_folder = os.path.join(destination_base_path, folder_name)

            # Ensure the destination ASXXXXX folder exists
            os.makedirs(destination_folder, exist_ok=True)

            # Iterate through subfolders (ports)
            for subfolder_name in os.listdir(source_folder):
                subfolder_path = os.path.join(source_folder, subfolder_name)
                if os.path.isdir(subfolder_path) and subfolder_name.isdigit():
                    eol_file = os.path.join(subfolder_path, "server_eol_success.json")
                    if os.path.isfile(eol_file):
                        # Define the destination file path
                        destination_file = os.path.join(destination_folder, f"eol_{subfolder_name}.json")
                        # Copy and rename the file
                        shutil.copy(eol_file, destination_file)
                        print(f"Copied: {eol_file} -> {destination_file}")

# Example usage
source_base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip"
destination_base_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_nick"
copy_eol_files(source_base_path, destination_base_path)