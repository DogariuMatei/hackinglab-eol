import sys
import json
from pathlib import Path
from intervaltree import IntervalTree, Interval
from collections import defaultdict
import requests

class CVE:
    def __init__(self, cve_id: str, exploitability_score: str):
        self.cve_id = cve_id
        self.exploitability_score = exploitability_score

    def __repr__(self):
        return f"CVE(cve_id={self.cve_id}, exploitability_score={self.exploitability_score})"

class Version:
    def __init__(self, parts):
        self.parts = parts

    @staticmethod
    def parse(version_str: str):
        return Version([int(p) if p.isdigit() else 0 for p in version_str.split('.')])

def version_to_int(version: Version) -> int:
    parts = version.parts[:3] + [0] * (3 - len(version.parts))
    return parts[0] * 1000000 + parts[1] * 1000 + parts[2]

def extract_product(cpe: str) -> str | None:
    parts = cpe.split(":")
    if len(parts) > 4:
        return parts[4].lower()
    return None

def extract_version(cpe: str) -> str | None:
    parts = cpe.split(":")
    if len(parts) > 5 and parts[5] != "*":
        return parts[5]
    return None

class CVEIndex:
    def __init__(self):
        self.data = defaultdict(IntervalTree)

    @staticmethod
    def build_from_json_file(path: Path):
        with open(path, "r", encoding="utf-8") as f:
            parsed = json.load(f)

        index = CVEIndex()
        for key, entry in parsed.get("fkie_nvd", []):
            cve_id = entry.get("id")
            exploitability_score = None

            if entry.get("metrics") and "cvssMetricV2" in entry.get("metrics"):
                for metric in entry.get("metrics")["cvssMetricV2"]:
                    if metric.get("type") == "Primary":
                        exploitability_score = metric.get("exploitabilityScore", None)
                        break
            elif entry.get("metrics") and "cvssMetricV31" in entry.get("metrics"):
                for metric in entry.get("metrics")["cvssMetricV31"]:
                    if metric.get("type") == "Primary":
                        exploitability_score = metric.get("exploitabilityScore", None)
                        break

            configurations = entry.get("configurations", [])
            for config in configurations:
                for node in config.get("nodes", []):
                    for cpe in node.get("cpeMatch", []):
                        if not cpe.get("vulnerable", False):
                            continue

                        product = extract_product(cpe["criteria"])
                        if not product:
                            continue

                        start = cpe.get("versionStartIncluding")
                        start = version_to_int(Version.parse(start)) if start else (
                            version_to_int(Version.parse(extract_version(cpe["criteria"]))) if extract_version(cpe["criteria"]) else 0
                        )

                        end = cpe.get("versionEndExcluding")
                        end_incl = cpe.get("versionEndIncluding")

                        if end:
                            end = version_to_int(Version.parse(end))
                        elif end_incl:
                            end = version_to_int(Version.parse(end_incl)) + 1
                        else:
                            ver = extract_version(cpe["criteria"])
                            end = version_to_int(Version.parse(ver)) + 1 if ver else 999_999_999

                        if start >= end:
                            continue

                        cve = CVE(cve_id, exploitability_score)
                        index.data[product].add(Interval(start, end, cve))
        return index

    def find_cves(self, product: str, version: str):
        product = product.lower()
        version_num = version_to_int(Version.parse(version))
        tree = self.data.get(product)
        if not tree:
            return []

        seen = set()
        results = []
        for iv in tree.at(version_num):
            if iv.data.cve_id not in seen:
                seen.add(iv.data.cve_id)
                results.append(iv.data)
        return results

def fetch_and_cache_json(dir, vendor: str, product: str) -> Path:
    url = f"https://cve.circl.lu/api/search/{vendor}/{product}"
    cache_file = dir / f"{vendor}_{product}.json"

    if cache_file.exists():
        print(f"Using cached file: {cache_file}")
        return cache_file

    print(f"Fetching from: {url}")
    response = requests.get(url)
    response.raise_for_status()
    text = response.text

    dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(text, encoding="utf-8")
    print(f"Cached to: {cache_file}")
    return cache_file

class CVEIndexManager:
    def __init__(self):
        self.indexes = {}

    def load_all_from_folder(self, folder: Path):
        for file in folder.glob("*.json"):
            product_name = "_".join(file.stem.split("_")[1:])
            print(f"Loading {file.name} for product: {product_name}")
            try:
                index = CVEIndex.build_from_json_file(file)
                self.indexes[product_name] = index
            except Exception as e:
                print(f"Failed to load {file}: {e}")

    def download_missing_indexes(self, folder: Path):
        vendor_products = [
            ("php", "php"),
            ("openssl", "openssl"),
            ("python", "python"),
            ("apache", "http_server"),
            ("f5", "nginx"),
            ("exim", "exim"),
            ("proftpd", "proftpd"),
            ("broadcom", "rabbitmq_server"),
            ("oracle", "mysql"),
            ("mariadb", "mariadb"),
            ("mongodb", "mongodb"),
            ("redis", "redis"),
            ("microsoft", "sql_server")
        ]

        for (vendor, product) in vendor_products:
            fetch_and_cache_json(folder, vendor, product)

    def find_cves(self, product: str, version: str) -> list:
        product = product.lower()
        index = self.indexes.get(product)
        if not index:
            print(f"No index found for product: {product}")
            return []
        return index.find_cves(product, version)

def get_product_mapping(server_name):
    mapping = {
        "apache": "http_server",
        "rabbitmq": "rabbitmq_server",
        "exim": "exim",
        "nginx": "nginx",
        "mariadb": "mariadb",
        "mongodb": "mongodb",
        "openssl": "openssl",
        "mysql": "mysql",
        "php": "php",
        "proftpd": "proftpd",
        "python": "python",
        "mod_python": "python",
        "redis": "redis",
        "mssql": "sql_server",
    }
    return mapping.get(server_name, server_name)

def run_search():
    if len(sys.argv) < 2:
        print("Usage: python script.py input.json")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    with open(input_path, "r") as f:
        entries = json.load(f)

    folder = Path("./cve_indexes")
    manager = CVEIndexManager()
    manager.download_missing_indexes(folder)
    manager.load_all_from_folder(folder)

    for entry in entries:
        product = get_product_mapping(entry.get("server", "").lower())
        version = entry.get("version", "")

        cves = manager.find_cves(product, version)

        entry["cves"] = [
            {
                "cve_id": cve.cve_id,
                "exploitability_score": cve.exploitability_score,
            }
            for cve in cves
        ]

    print(json.dumps(entries, indent=2))
    output_path = input_path.with_name(f"{input_path.stem}_cves.json")
    with open(output_path, "w") as out_file:
        json.dump(entries, out_file, indent=2)
    print(f"Output written to {output_path}")

# if __name__ == "__main__":
#     run_search()


def process_file(input, output):
    input_path = Path(input)
    with open(input_path, "r") as f:
        entries = json.load(f)

    folder = Path("./cve_indexes")
    manager = CVEIndexManager()
    manager.download_missing_indexes(folder)
    manager.load_all_from_folder(folder)

    for entry in entries:
        product = get_product_mapping(entry.get("server", "").lower())
        version = entry.get("version", "")

        cves = manager.find_cves(product, version)

        entry["cves"] = [
            {
                "cve_id": cve.cve_id,
                "exploitability_score": cve.exploitability_score,
            }
            for cve in cves
        ]

    # print(json.dumps(entries, indent=2))
    with open(output, "w") as out_file:
        json.dump(entries, out_file, indent=2)
    print(f"Output written to {output}")
