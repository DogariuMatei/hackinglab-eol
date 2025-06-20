#!/bin/bash

set -e

# Step 1: Copy-Paste IPv4 range of your AS (https://hackertarget.com/as-ip-lookup/) (if its NOT already created - from the auto script)
# Step 2: Change variable AS_NUMBER to the AS you're scanning now
# DO NOT CHANGE PORTS_FILE
AS_NUMBER="20847"
IP_LIST="${AS_NUMBER}-ips.txt"
PORTS_FILE="manual-ports.txt"

get_ports() {
    cat "$PORTS_FILE" | tr ',' '\n'
}

for port in $(get_ports); do
    echo "Scanning port $port"

    mkdir -p "Port${port}"

    sudo zmap -p "$port" -o "AS${AS_NUMBER}Port${port}/zmap_output.csv" -r 128 -w "$IP_LIST"
done

echo "Done"