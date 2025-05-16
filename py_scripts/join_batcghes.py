import json
import glob


def join_batch_files(output_path="nl_domains_nl_ips_only.json"):
    """Join all batch JSON files into one complete file"""

    # Pattern to find all batch files
    batch_pattern = f"{output_path}.batch*"
    batch_files = sorted(glob.glob(batch_pattern))

    if not batch_files:
        print("No batch files found to join.")
        return

    print(f"Found {len(batch_files)} batch files to join.")

    # Combined dictionary for all domains
    combined_data = {}

    # Process each batch file
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r') as file:
                batch_data = json.load(file)
                combined_data.update(batch_data)
                print(f"Added {len(batch_data)} domains from {batch_file}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error processing {batch_file}: {e}")

    # Write the combined data to the output file
    with open(output_path, 'w') as file:
        json.dump(combined_data, file, indent=2)

    print(f"Successfully joined all batches into {output_path} with {len(combined_data)} domains.")


# Direct execution - no main block
output_file = "nl_domains_nl_ips_only.json"
join_batch_files(output_file)