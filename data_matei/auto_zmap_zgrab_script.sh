#!/bin/bash

set -e

AS_NUMBER="31477"
IP_LIST="31477-ips.txt"
PORTS_FILE="auto-ports.txt"

# Get the real user (not root when using sudo)
REAL_USER=${SUDO_USER:-$USER}

# Get ports from file
get_ports() {
    cat "$PORTS_FILE" | tr ',' '\n'
}

# Get zgrab2 command for port
get_zgrab_command() {
    local port=$1
    local output_file="AS${AS_NUMBER}Port${port}/zgrab_results.json"

    case $port in
        80|443|8080)
            echo "zgrab2 http -p $port --user-agent \"Mozilla/5.0\" --senders=20 --endpoint \"/\" --output-file $output_file"
            ;;
        587|465)
            echo "zgrab2 smtp -p $port -t 20 --senders=20 --output-file $output_file"
            ;;
        21)
            echo "zgrab2 ftp -p $port --senders=20 --output-file $output_file"
            ;;
        993)
            echo "zgrab2 imap -p $port --imaps -t 20 --senders=20 --output-file $output_file"
            ;;
        995)
            echo "zgrab2 pop3 -p $port --pop3s -t 20 --senders=20 --output-file $output_file"
            ;;
        1433)
            echo "zgrab2 mssql -p $port -t 20 --senders=20 --output-file $output_file"
            ;;
    esac
}

# Process each port
for port in $(get_ports); do
    echo "Processing port $port"

    # Create directory
    mkdir -p "AS${AS_NUMBER}Port${port}"

    # Run zmap
    zmap -p "$port" -o "AS${AS_NUMBER}Port${port}/zmap_output.csv" -r 128 -w "$IP_LIST"

    # Run zgrab2 if zmap found results
    if [[ -s "AS${AS_NUMBER}Port${port}/zmap_output.csv" ]]; then
        zgrab_cmd=$(get_zgrab_command "$port")
        if [[ -n "$zgrab_cmd" ]]; then
            cat "AS${AS_NUMBER}Port${port}/zmap_output.csv" | eval "$zgrab_cmd"
        fi
    fi

    # Fix permissions for this port's directory
    chown -R $REAL_USER:$REAL_USER "AS${AS_NUMBER}Port${port}"
done

# Fix permissions for entire directory at the end
chown -R $REAL_USER:$REAL_USER .

echo "Done"