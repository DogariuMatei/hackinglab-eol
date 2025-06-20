# Network Security Scanner
## Installation
### Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Scan an entire ASN:
```bash
python src/main.py --asn AS15169
```

Scan custom IP list:
```bash
python src/main.py --custom-ips ips.txt
```

### Command Line Options

```
usage: main.py [-h] (--asn ASN | --custom-ips CUSTOM_IPS)

Scan services based on IPs from ASN or custom IP list.

options:
  -h, --help            show this help message and exit
  --asn ASN             ASN to look up (example: AS12345)
  --custom-ips CUSTOM_IPS
                        Path to a file containing IP addresses to scan (example: ips.txt)
```

### Input File Format

For custom IP lists, provide a text file with one IP address or CIDR range per line:
```
192.168.1.0/24
10.0.0.1
203.0.113.0/24
```

## Architecture

### Components:

#### 1. **ASN Lookup** (`asn_lookup.py`)
- Resolves ASN numbers to IP prefixes using HackerTarget API
- Supports both cached and live lookups

#### 2. **Network Scanning** (`zmap.py`)
- Wrapper around zmap for port scanning
- Automatically detects gateway MAC address
- Configurable scan rates and caching

#### 3. **Version Scanners** (`version_scanners/`)
- **ZGrab2 Scanner**: HTTP, SMTP, FTP, MSSQL, RabbitMQ detection
- **MySQL Scanner**: Direct MySQL/MariaDB protocol detection
- **Redis Scanner**: Redis INFO command execution
- **MongoDB Scanner**: MongoDB server information retrieval

#### 4. **Final Analysis**
- **EOL Checker** (`eol_checker.py`): Identifies end-of-life software versions
- **CVE Finder** (`cve_finder.py`): Maps software versions to known vulnerabilities
- **TLS Checker** (`tls_checker.py`): Analyzes TLS protocol versions

### Services & Ports

| Service | Ports | Scanner | Detection Method |
|---------|-------|---------|------------------|
| HTTP | 80, 8080 | ZGrab2 | Server headers |
| HTTPS | 443 | ZGrab2 | Server headers + TLS |
| SMTP | 587, 465 | ZGrab2 | Banner parsing |
| FTP | 21 | ZGrab2 | Banner analysis |
| MySQL | 3306 | Custom | Protocol handshake |
| MongoDB | 27017 | Custom | Server info command |
| Redis | 6379 | Custom | INFO command |
| MSSQL | 1433 | ZGrab2 | Version detection |
| RabbitMQ | 5671, 5672 | ZGrab2 | AMQP properties |
| IMAP | 993 | ZGrab2 | Secure IMAP |
| POP3 | 995 | ZGrab2 | Secure POP3 |

## Output Structure

The tool generates structured output in the following locations:

### Directory Structure
```
cache/
├── asn/                   # Cached ASN to IP mappings
├── zmap/                  # Zmap scan results
├── version-scanner/       # Service version detection results
├── eol/                   # End-of-life check results
│   ├── success/           # Successfully checked versions
│   └── failure/           # Failed EOL lookups
└── cve_indexes/           # CVE database cache

results/
├── tls/                   # TLS version analysis
└── [ASN]-[port].json      # Final results with CVEs - this is main results
```

### Output Format

Each result file contains JSON arrays with entries like (for each unique IP):

```json
{
  "ip": "203.0.113.1",
  "server": "nginx",
  "version": "1.18",
  "api_name": "nginx",
  "original_server": "nginx/1.18.0",
  "is_eol": true,
  "eol_from": "2022-05-31",
  "status": "EOL: true, EOL Date: 2022-05-31",
  "cves": [
    {
      "cve_id": "CVE-2022-41741",
      "exploitability_score": 3.9,
      "impact_score": 2.9
    }
  ]
}
```

## Configuration

### Scanner Configuration

Edit `src/main.py` to modify scanner settings:

```python
# Modify port mappings
scanner_map[80] = [ZGrab2(["http", "--user-agent", "Mozilla/5.0"], 80, http_version_extractor)]

# Adjust scan rates in zmap.py
self.rate = 128  # packets per second

# Modify timeouts in custom scanners
self.timeout = 3  # seconds
```

## Docker Support

Build and run using Docker:

```bash
# Build image
docker build -t network-scanner .

# Run scan
docker run -v $(pwd)/results:/app/results network-scanner --asn AS15169
```

## Troubleshooting

### Common Issues

**Permission denied for zmap:**
```bash
sudo setcap cap_net_raw=eip /usr/bin/zmap
```

**Gateway MAC detection fails:**
```bash
# Manually set in zmap.py
self.gateway_mac = "aa:bb:cc:dd:ee:ff"
```