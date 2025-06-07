import os
import json
import csv

def combine_clean_versions(konstantin_path, filip_path, output_path):
    os.makedirs(output_path, exist_ok=True)

    for filename in os.listdir(konstantin_path):
        if filename.startswith("parsed_") and filename.endswith(".json"):
            port = filename.split("_")[1].split(".")[0]
            konstantin_file = os.path.join(konstantin_path, filename)
            filip_file = os.path.join(filip_path, port, "clean_versions.json")
            output_file = os.path.join(output_path, f"combined_clean_versions_{port}.json")

            combined_data = []

            # Read Konstantin's file
            try:
                with open(konstantin_file, "r", encoding="utf-8") as f:
                    konstantin_data = json.load(f)
                    combined_data.extend(konstantin_data)
            except Exception as e:
                print(f"Error reading {konstantin_file}: {e}")

            # Read Filip's file
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


def combine_zmap_files(konstantin_path, filip_path, output_path):
    os.makedirs(output_path, exist_ok=True)

    for filename in os.listdir(konstantin_path):
        if filename.startswith("zmap_") and filename.endswith(".csv"):
            port = filename.split("_")[1].split(".")[0]
            konstantin_file = os.path.join(konstantin_path, filename)
            filip_file = os.path.join(filip_path, port, f"zmap_output.csv")
            output_file = os.path.join(output_path, f"combined_zmap_{port}.csv")

            combined_data = []

            # Read Konstantin's file
            try:
                with open(konstantin_file, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    combined_data.extend(list(reader))
            except Exception as e:
                print(f"Error reading {konstantin_file}: {e}")

            # Read Filip's file
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


if __name__ == "__main__":
    # Paths
    konstantin_clean_versions = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data\clean_versions"
    konstantin_zmap = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_konstantin\All_port_data\zmap"
    filip_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\AS57043"
    output_path = r"D:\Uni\Y4Q4\HackingLab\hackinglab-eol\data_filip\combined_data"

    # Combine clean_versions
    # combine_clean_versions(konstantin_clean_versions, filip_path, output_path)

    # Combine zmap files
    combine_zmap_files(konstantin_zmap, filip_path, output_path)