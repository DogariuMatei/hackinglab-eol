#!/bin/bash

# Simple zmap-only scanner
set -e

AS_NUMBER="20847"
IP_LIST="20847-ips.txt"
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