#!/bin/bash

# Simple zmap-only scanner
set -e

IP_LIST="previder-ips.txt"
PORTS_FILE="ports2.txt"

# Get ports from file
get_ports() {
    cat "$PORTS_FILE" | tr ',' '\n'
}

for port in $(get_ports); do
    echo "Scanning port $port"

    mkdir -p "Port${port}"

    sudo zmap -p "$port" -o "Port${port}/zmap_output.csv" -r 128 -w "$IP_LIST"
done

echo "Done"