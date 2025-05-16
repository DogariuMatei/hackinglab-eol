import csv
import json
import sys


def filter_nl_domains(csv_file_path, output_file_path="nl_domains.json"):
    nl_domains = []

    try:
        with open(csv_file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                domain = row['Domain']
                if domain.endswith('.nl'):
                    nl_domains.append(domain)
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
        sys.exit(1)

    # Write to JSON file
    with open(output_file_path, 'w') as json_file:
        json.dump(nl_domains, json_file, indent=2)

    print(f"Filtered domains have been saved to {output_file_path}")


# Usage: Provide the path to your CSV file as the first argument
# and optionally the output JSON file as the second argument
if len(sys.argv) > 1:
    file_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        filter_nl_domains(file_path, output_path)
    else:
        filter_nl_domains(file_path)
else:
    file_path = "top10milliondomains.csv"
    filter_nl_domains(file_path)