import json
import csv
import sys


def prepare_zgrab_input(input_json_file, output_csv_file):
    """
    Convert a JSON file with domains and IPs to the zgrab CSV format
    with only IP and DOMAIN columns

    Expected JSON format:
    {
        "domain1.nl": ["1.2.3.4", "5.6.7.8"],
        "domain2.nl": ["9.10.11.12"]
    }

    Output CSV format:
    IP,DOMAIN
    1.2.3.4,domain1.nl
    5.6.7.8,domain1.nl
    9.10.11.12,domain2.nl
    """
    try:
        # Load the input JSON file
        with open(input_json_file, 'r') as f:
            domains_with_ips = json.load(f)

        print(f"Loaded {len(domains_with_ips)} domains from {input_json_file}")

        # Open the output CSV file
        with open(output_csv_file, 'w', newline='') as f:
            writer = csv.writer(f)

            # Process each domain and its IPs
            total_entries = 0
            for domain, ips in domains_with_ips.items():
                for ip in ips:
                    # Write a row for each IP-domain pair (just IP and DOMAIN)
                    writer.writerow([ip, domain])
                    total_entries += 1

        print(f"Successfully wrote {total_entries} entries to {output_csv_file}")

    except FileNotFoundError:
        print(f"Error: Could not find input file {input_json_file}")
        return False
    except json.JSONDecodeError:
        print(f"Error: {input_json_file} is not a valid JSON file")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

    return True


# Input and output file paths
input_json_file = "nl_domains_nl_ips_only.json"
output_csv_file = "zgrab_targets.csv"

# Run the conversion
print(f"Converting {input_json_file} to zgrab-compatible format in {output_csv_file}")
prepare_zgrab_input(input_json_file, output_csv_file)