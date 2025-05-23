#!/bin/bash

# Set this once to change the suffix used in all filenames
SUFFIX="AS8315"

# Run ZMap scan
sudo zmap -p 80 -o "zmap_output${SUFFIX}.csv" -r 1024 -w "IP${SUFFIX}.txt"

# Run ZGrab2
cat "zmap_output${SUFFIX}.csv" | ../zgrab2/zgrab2 http \
  --user-agent "Mozilla/5.0" \
  --endpoint "/" \
  --output-file "zgrab_results${SUFFIX}.json"

# Extract and clean server versions
cat "zgrab_results${SUFFIX}.json" | jq -c \
  'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
  | {server: .data.http.result.response.headers.server[0], ip: .ip}' \
  | jq -s '.' > "clean_versions${SUFFIX}.json"

# Count and sort by server
cat "clean_versions${SUFFIX}.json" | jq \
  'group_by(.server)
  | map({server: .[0].server, count: length})
  | sort_by(-.count)
  | .[]
  | "\(.server): \(.count)"' > "clean_count${SUFFIX}.json"
