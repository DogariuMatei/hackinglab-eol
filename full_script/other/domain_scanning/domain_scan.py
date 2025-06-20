import csv
import os
import json
import socket
import concurrent.futures
from tqdm import tqdm
import subprocess
import requests
import zipfile

MAX_WORKERS = 300
MAX_CONCURRENT_IP_INFO_REQUESTS = 100
IP_INFO_API_TOKEN = "<your_token_here>"
COUNTRY_CODE = "NL"
OUTPUT_FILE = "zgrab_targets.csv"

### Download top 10 million domains
print("[1/4] Getting data")

url = "https://www.domcop.com/files/top/top10milliondomains.csv.zip"
zip_filename = "top10milliondomains.csv.zip"
csv_filename = "top10milliondomains.csv"

# Download the ZIP file only if it doesn't already exist
if not os.path.isfile(zip_filename):
    print("Downloading top10milliondomains.csv.zip file")
    response = requests.get(url)
    if response.status_code == 200:
        with open(zip_filename, "wb") as f:
            f.write(response.content)
        print("Download complete.")
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")
else:
    print(f"{zip_filename} already exists. Skipping download.")

# Extract the CSV file only if it doesn't already exist
if not os.path.isfile(csv_filename):
    print("Extracting top10milliondomains.csv file")
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extract(csv_filename)
    print(f"CSV file extracted: {csv_filename}")
else:
    print(f"{csv_filename} already exists. Skipping extraction.")

### Filter .nl domains
print("[2/4] Filtering .nl domains and prefixing with www.")

nl_domains = []
with open(csv_filename, 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        domain = row['Domain']
        if domain.endswith('.nl'):
            nl_domains.append(domain)

### Prefix domains with www.
www_nl_domains = ["www." + domain for domain in nl_domains]

### Resolve domain IPs
print("[3/4] Resolve domain IPs")

domains_with_ips = {}

def resolve_domain(domain):
    """Resolve a single domain to its IP addresses"""
    try:
        # Using gethostbyname_ex to get all IP addresses
        _, _, ips = socket.gethostbyname_ex(domain)
        return domain, ips
    except:
        return domain, []

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(resolve_domain, domain): domain for domain in www_nl_domains}

    for future in tqdm(concurrent.futures.as_completed(futures), total=len(www_nl_domains)):
        domain, ips = future.result()
        domains_with_ips[domain] = ips

### Filter the IPs that are in the Netherlands
print("[3/4] Filtering the IPs that are in the Netherlands")

filtered_domains = {}

def is_ip_in_country(ip_address, country_code):
    try:
        response = subprocess.run(['curl', '-s', f'https://api.ipinfo.io/lite/{ip_address}?token=c79342059ea2c4'],
                                  capture_output=True, text=True)
        data = json.loads(response.stdout)
        return data.get('country_code') == country_code
    except Exception as e:
        print(f"Exception checking IP {ip_address}: {e}")
        return False

def process_ip(ip_data):
    domain, ip = ip_data
    is_in_country = is_ip_in_country(ip, COUNTRY_CODE)
    return domain, ip, is_in_country

all_ip_tasks = []
for domain, ips in domains_with_ips.items():
    for ip in ips:
        all_ip_tasks.append((domain, ip))

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_IP_INFO_REQUESTS) as executor:
    futures = [executor.submit(process_ip, ip_data) for ip_data in all_ip_tasks]

    for future in tqdm(concurrent.futures.as_completed(futures), total=len(all_ip_tasks)):
        try:
            domain, ip, is_in_country = future.result()

            if is_in_country:
                if domain not in filtered_domains:
                    filtered_domains[domain] = []
                filtered_domains[domain].append(ip)

        except Exception as e:
            print(f"Error processing IP: {e}")


### Save the result as a ZGrab2 input
print("[4/4] Saving the targets as a ZGrab2 input")

with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)

    total_entries = 0
    for domain, ips in filtered_domains.items():
        for ip in ips:
            writer.writerow([ip, domain])
            total_entries += 1

print(f"[4/4] Found {total_entries} targets")
