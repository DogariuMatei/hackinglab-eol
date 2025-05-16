import json
import socket
import concurrent.futures
from tqdm import tqdm

# Hardcoded file paths
INPUT_JSON_PATH = "nl_domains.json"
OUTPUT_JSON_PATH = "nl_domains_with_ips.json"

# Hardcoded parameters
MAX_WORKERS = 300
BATCH_SIZE = 5000


def resolve_domain(domain):
    """Resolve a single domain to its IP addresses"""
    try:
        # Using gethostbyname_ex to get all IP addresses
        _, _, ips = socket.gethostbyname_ex(domain)
        return domain, ips
    except (socket.gaierror, socket.herror) as e:
        # Handle DNS resolution errors
        return domain, []


def batch_save(domains_with_ips, batch_num):
    """Save results in batches to prevent data loss in case of crashes"""
    temp_output_path = f"{OUTPUT_JSON_PATH}.batch{batch_num}"
    with open(temp_output_path, 'w') as file:
        json.dump(domains_with_ips, file)
    print(f"Saved batch {batch_num} with {len(domains_with_ips)} domains")


# Load domains from JSON file
try:
    with open(INPUT_JSON_PATH, 'r') as file:
        domains = json.load(file)
except FileNotFoundError:
    print(f"Error: File '{INPUT_JSON_PATH}' not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: File '{INPUT_JSON_PATH}' is not valid JSON.")
    exit(1)

total_domains = len(domains)
print(f"Resolving IP addresses for {total_domains} domains using {MAX_WORKERS} threads...")

domains_with_ips = {}
count = 0
batch_count = 0

# Create a thread pool executor with 300 threads
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all domains for resolution
    futures = {executor.submit(resolve_domain, domain): domain for domain in domains}

    # Process results as they complete with a progress bar
    for future in tqdm(concurrent.futures.as_completed(futures), total=total_domains):
        domain, ips = future.result()
        domains_with_ips[domain] = ips

        # Save in batches to prevent data loss
        count += 1
        if count % BATCH_SIZE == 0:
            batch_count += 1
            batch_save(domains_with_ips, batch_count)

# Write the final results
with open(OUTPUT_JSON_PATH, 'w') as file:
    json.dump(domains_with_ips, file, indent=2)

print(f"Completed! All {len(domains_with_ips)} domains with IP addresses saved to {OUTPUT_JSON_PATH}")