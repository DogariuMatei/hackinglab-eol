import json
import subprocess
import concurrent.futures
from tqdm import tqdm
import os

# Hardcoded file paths
INPUT_JSON_PATH = "nl_domains_with_ips.json"
OUTPUT_JSON_PATH = "nl_domains_nl_ips_only.json"

# Hardcoded parameters
MAX_CONCURRENT_REQUESTS = 100  # Higher concurrency for speed
COUNTRY_CODE = "NL"  # Netherlands country code
CHUNK_SIZE = 500  # Process in chunks of 500 IPs at a time


def is_ip_in_country(ip_address, country_code):
    """
    Check if the given IP address is located in the specified country using the ipinfo.io API.

    :param ip_address: The IP address to check
    :param country_code: The country code to check
    :return: True if the IP is in the specified country, False otherwise
    """
    try:
        response = subprocess.run(['curl', '-s', f'https://api.ipinfo.io/lite/{ip_address}?token=c79342059ea2c4'],
                                  capture_output=True, text=True)
        data = json.loads(response.stdout)
        return data.get('country_code') == country_code
    except Exception as e:
        print(f"Exception checking IP {ip_address}: {e}")
        return False


def process_ip(ip_data):
    """Process a single IP and check if it's in the target country"""
    domain, ip = ip_data
    is_in_country = is_ip_in_country(ip, COUNTRY_CODE)
    return domain, ip, is_in_country


def main():
    # Load the domains with IPs from the JSON file
    try:
        with open(INPUT_JSON_PATH, 'r') as file:
            domains_with_ips = json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{INPUT_JSON_PATH}' not found.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: File '{INPUT_JSON_PATH}' is not valid JSON.")
        exit(1)

    print(f"Filtering {len(domains_with_ips)} domains to keep only {COUNTRY_CODE} IPs...")

    # Prepare a list of all (domain, ip) pairs for processing
    all_ip_tasks = []
    for domain, ips in domains_with_ips.items():
        for ip in ips:
            all_ip_tasks.append((domain, ip))

    print(f"Total IPs to check: {len(all_ip_tasks)}")

    # Dictionary to store results
    filtered_domains = {}

    # Process IPs in chunks to avoid overwhelming resources
    for i in range(0, len(all_ip_tasks), CHUNK_SIZE):
        chunk = all_ip_tasks[i:i + CHUNK_SIZE]
        print(f"Processing chunk {i // CHUNK_SIZE + 1}/{(len(all_ip_tasks) - 1) // CHUNK_SIZE + 1} ({len(chunk)} IPs)")

        # Process this chunk in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
            futures = [executor.submit(process_ip, ip_data) for ip_data in chunk]

            # Process results as they complete
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(chunk)):
                try:
                    domain, ip, is_in_country = future.result()

                    # If the IP is in the target country, add it to results
                    if is_in_country:
                        if domain not in filtered_domains:
                            filtered_domains[domain] = []
                        filtered_domains[domain].append(ip)

                except Exception as e:
                    print(f"Error processing IP: {e}")

        # Save progress after each chunk
        with open(f"{OUTPUT_JSON_PATH}.progress", 'w') as file:
            json.dump(filtered_domains, file, indent=2)

        print(f"Progress: Found {len(filtered_domains)} domains with {COUNTRY_CODE} IPs so far")

    # Write the final results
    with open(OUTPUT_JSON_PATH, 'w') as file:
        json.dump(filtered_domains, file, indent=2)

    # Remove the progress file
    if os.path.exists(f"{OUTPUT_JSON_PATH}.progress"):
        os.remove(f"{OUTPUT_JSON_PATH}.progress")

    print(f"Completed! Found {len(filtered_domains)} domains with at least one {COUNTRY_CODE} IP.")
    print(f"Results saved to {OUTPUT_JSON_PATH}")


# Run the script
main()