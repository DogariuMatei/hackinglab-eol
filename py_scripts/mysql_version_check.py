import csv
import json
import socket
import re
import mysql.connector

def extract_mariadb_version(version_string):
    mariadb_match = re.search(r'5\.5\.5-(\d+\.\d+\.\d+)', version_string)
    if mariadb_match:
        return mariadb_match.group(1)
    mariadb_match = re.search(r'(\d+\.\d+\.\d+)-MariaDB', version_string)
    if mariadb_match:
        return mariadb_match.group(1)
    return None

def extract_mysql_version(version_string):
    mysql_match = re.search(r'(\d+\.\d+\.\d+)', version_string)
    if mysql_match:
        return mysql_match.group(1)
    return None

def get_mysql_or_mariadb_version(ip, port=3306, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        data = s.recv(4096)
        s.close()
        data_str = data.decode('utf-8', errors='ignore')

        if "MariaDB" in data_str:
            version = extract_mariadb_version(data_str)
            return ("MariaDB", version) if version else ("MariaDB", None)
        if len(data) > 5:
            pos = 5
            version_end = data.find(b'\0', pos)
            if version_end > pos:
                full_version = data[pos:version_end].decode('utf-8', errors='ignore')
                version = extract_mysql_version(full_version)
                return ("MySQL", version) if version else ("MySQL", None)
    except Exception:
        pass

    try:
        connection = mysql.connector.connect(
            host=ip,
            port=port,
            user="root",
            password="",
            connection_timeout=timeout
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION();")
            full_version = cursor.fetchone()[0]
            cursor.close()
            connection.close()

            if "MariaDB" in full_version:
                version = extract_mariadb_version(full_version)
                return ("MariaDB", version) if version else ("MariaDB", None)
            else:
                version = extract_mysql_version(full_version)
                return ("MySQL", version) if version else ("MySQL", None)
    except Exception:
        pass

    return (None, None)

results = []
with open('AAS20857/zmap_output/output_AS20857_mysql.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ip = row[0]
        product, version = get_mysql_or_mariadb_version(ip)

        if product and version:
            server_val = f"{product}/{version}"
        elif product:
            server_val = product
        else:
            continue

        entry = {
            "ip": ip,
            "server": server_val
        }
        results.append(entry)
        print(f"Checked {ip}: {server_val}")

output_filename = "AAS20857/clean_version_ip/mysql_versions_AS20857_3june.json"
with open(output_filename, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"\nResults saved to {output_filename}")