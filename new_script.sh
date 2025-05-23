#!/bin/bash

# === CONFIGURATION ===
SUFFIX="AS57043"
PORT="443"
RATE="1024"

# === PATH SETUP ===
BASE_DIR="data_filip/${SUFFIX}/${PORT}"
mkdir -p "$BASE_DIR"

ZMAP_OUTPUT="${BASE_DIR}/zmap_output${SUFFIX}.csv"
IP_LIST="data_filip/${SUFFIX}/IP${SUFFIX}.txt"
ZGRAB_OUTPUT="${BASE_DIR}/zgrab_results${SUFFIX}.json"
CLEAN_VERSIONS="${BASE_DIR}/clean_versions${SUFFIX}.json"
CLEAN_COUNT="${BASE_DIR}/clean_count${SUFFIX}.json"

# === ZMAP ===
sudo zmap -p "$PORT" -o "$ZMAP_OUTPUT" -r "$RATE" -w "$IP_LIST"

# === ZGRAB2 ===
cat "$ZMAP_OUTPUT" | ../zgrab2/zgrab2 --senders 20 http \
  --user-agent "Mozilla/5.0" \
  --endpoint "/" \
  --output-file "$ZGRAB_OUTPUT"

# === FILTER & CLEAN JSON ===
cat "$ZGRAB_OUTPUT" | jq -c \
  'select(.data.http.result.response.headers.server != null and .data.http.result.response.headers.server[0] != null)
   | {server: .data.http.result.response.headers.server[0], ip: .ip}' \
  | jq -s '.' > "$CLEAN_VERSIONS"

# === GROUP AND COUNT ===
cat "$CLEAN_VERSIONS" | jq \
  'group_by(.server)
   | map({server: .[0].server, count: length})
   | sort_by(-.count)
   | .[]
   | "\(.server): \(.count)"' > "$CLEAN_COUNT"
