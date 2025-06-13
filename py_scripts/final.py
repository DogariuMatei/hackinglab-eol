from os import mkdir
from pathlib import Path

import process_results as http
import smpt_parser as smptp
import ftpd_parser as ftp
import rabbitmq_parser as rabbitmq
import mssql_parser as mssql
import tls_parser as tls
import best_eol_parralel as eol_cached
import cve_finder as cve

directory = Path('../eol-finder/cache/version-scanner/zgrab2')
files = [f.name for f in directory.iterdir() if f.is_file()]

mkdir('./output')

http_files = [file for file in files if (file.endswith("80.txt") or file.endswith("8080.txt") or file.endswith("443.txt"))]
for file in http_files:
    http.process_json_file(str(directory / file), './output/' + file)

smtp_files = [file for file in files if (file.endswith("25.txt") or file.endswith("587.txt") or file.endswith("465.txt"))]
for file in smtp_files:
    smptp.process_file(str(directory / file), './output/' + file)

ftp_files = [file for file in files if file.endswith("-21.txt")]
for file in ftp_files:
    ftp.process_file(str(directory / file), './output/' + file)

# pop3_files = [file for file in files if file.endswith("995.txt")]

# oracle_files = [file for file in files if file.endswith("1521.txt")]

mssql_files = [file for file in files if file.endswith("1433.txt")]
for file in mssql_files:
    mssql.process_file(str(directory / file), './output/' + file)

# imap_files = [file for file in files if file.endswith("993.txt")]

amqp091_files = [file for file in files if (file.endswith("5671.txt") or file.endswith("5672.txt"))]
for file in ftp_files:
    rabbitmq.process_file(str(directory / file), './output/' + file)

# mkdir('./output/tls')

tls_files = [file for file in files if (file.endswith("993.txt") or file.endswith("995.txt") or file.endswith("-433.txt") or file.endswith("465.txt"))]
for file in tls_files:
    tls.process_file(str(directory / file), './output/tls/' + file.replace('.txt', '-tls.txt'))

directory = Path('./output/')
version_files = [f.name for f in directory.iterdir() if f.is_file()]
print(version_files)
mkdir('./output/eol/')
mkdir('./output/eolf/')
for file in version_files:
    eol_cached.process_file(str(directory / file), './output/eol/' + file, './output/eolf/' + file)

directory = Path('./output/eol')
eol_files = [f.name for f in directory.iterdir() if f.is_file()]

directory_data = Path('./data_georgi/')
mkdir(directory_data)
for file in eol_files:
    cve.process_file(str(directory / file), str(directory_data / file))
