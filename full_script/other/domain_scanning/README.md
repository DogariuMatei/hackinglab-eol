# NL Domain Scanner
This tool iterates over the top 10 million domains, selects the .nl ones, appends www. and resolves the IPs and filters the hosts that are only in the Netherlands.

## Installation
### Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

To run the script, an IPinfo API token is required. It can be acquired [here](https://ipinfo.io/developers).

```python
# Set the token within domain_scan.py
IP_INFO_API_TOKEN = "<your_token_here>"
```

Generates a zgrab_targets.csv file with the IPs from the Netherlands for some of the most popular domains
```bash
python domain_scan.py
```


The zgrab_targets.csv can then be used with main EOL and CVEs scanner with the --custom-ips argument.
