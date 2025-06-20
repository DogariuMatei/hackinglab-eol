#!/bin/bash

sudo zmap -p 80 -o "zmap_output.csv" -r 128 -w target-ips.csv


cat zmap_output.csv | ./zgrab2 http --user-agent "Mozilla/5.0" --endpoint "/" --output-file zgrab_results.json


cat zgrab_results.json | jq -c 'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
| {server: .data.http.result.response.headers.server[0], ip: .ip}' | jq -s '.' > clean_versions.json

cat clean_versions.json | jq 'group_by(.server) | map({server: .[0].server, count: length}) | sort_by(-.count) | .[] | "\(.server): \(.count)"' > clean_count.json
