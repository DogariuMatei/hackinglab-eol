import csv
import json
import socket
import re
import mysql.connector


def extract_mariadb_version(version_string):
    mariadb_match = re.search(r'5\.5\.5-(\d+\.\d+\.\d+)', version_string)
    if mariadb_match:
        return f"MariaDB {mariadb_match.group(1)}"

    mariadb_match = re.search(r'(\d+\.\d+\.\d+)-MariaDB', version_string)
    if mariadb_match:
        return f"MariaDB {mariadb_match.group(1)}"

    return "MariaDB"


def get_mysql_or_mariadb_version(ip, port=3306, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))

        data = s.recv(4096)
        s.close()

        data_str = data.decode('utf-8', errors='ignore')

        if "MariaDB" in data_str:
            return extract_mariadb_version(data_str)

        if len(data) > 5:
            pos = 4
            pos += 1

            version_end = data.find(b'\0', pos)
            if version_end > pos:
                full_version = data[pos:version_end].decode('utf-8', errors='ignore')
                version_match = re.search(r'^(\d+\.\d+\.\d+)', full_version)
                if version_match:
                    return f"MySQL {version_match.group(1)}"
    except socket.timeout:
        return "Connection Timeout"
    except ConnectionRefusedError:
        return "Connection Refused"
    except Exception as e:
        return f"Error: {str(e)}"

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
                return extract_mariadb_version(full_version)

            version_match = re.search(r'^(\d+\.\d+\.\d+)', full_version)
            if version_match:
                return f"MySQL {version_match.group(1)}"
            return f"MySQL {full_version}"
    except mysql.connector.Error as e:
        return f"MySQL Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

    return "Unknown"


results = []
with open('output_AS20857_mysql.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        ip = row[0]
        version = get_mysql_or_mariadb_version(ip)

        entry = {
            "ip": ip,
            "server": version
        }
        results.append(entry)
        print(f"Checked {ip}: {version}")

output_filename = "mysql_versions_AS20857.json"
with open(output_filename, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"\nResults saved to {output_filename}")